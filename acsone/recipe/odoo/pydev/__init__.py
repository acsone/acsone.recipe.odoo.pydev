# -*- coding: utf-8 -*-
#
#
#    Authors: Laurent Mignon
#    Copyright (c) 2014 Acsone SA/NV (http://www.acsone.eu)
#    All Rights Reserved
#
#    WARNING: This program as such is intended to be used by professional
#    programmers who take the whole responsibility of assessing all potential
#    consequences resulting from its eventual inadequacies and bugs.
#    End users who are looking for a ready-to-use solution with commercial
#    guarantees and support are strongly advised to contact a Free Software
#    Service Company.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#
import os
from os.path import join
import sys
import logging
import subprocess
import zc.buildout
import zc.recipe.egg
from anybox.recipe.openerp import devtools
from anybox.recipe.openerp.server import ServerRecipe

import xml.etree.ElementTree as ET
import shutil

logger = logging.getLogger(__name__)

SERVER_COMMA_LIST_OPTIONS = ('log_handler', )


class Recipe(ServerRecipe):
    """Recipe for pydev env install and config
    """

    def __init__(self, buildout, name, options):
        super(Recipe, self).__init__(buildout, name, options)
        self.options.setdefault('project-name', 'OpenErpServer')
        self.options.setdefault('python-version', 'python 2.7')
        self.options.setdefault('python-interpreter', 'Default')
        self.egg = zc.recipe.egg.Scripts(self.buildout, self.name, self.options)
        wd = self.buildout['buildout']['directory']
        self._wd_path = wd
        self._fpydev_path = self.options.get('pydevproject_path', wd)
        self._fpydev_pydevproject = os.path.join(self._fpydev_path, '.pydevproject')
        self._fpydev_project = os.path.join(self._fpydev_path, '.project')
        self._project_name = self.options["project-name"]
        self._omelette_name = self.name + "omelette_addons"
        self._omelette_path = os.path.join(self._wd_path,
                                           self.buildout['buildout']['parts-directory'],
                                           self._omelette_name)

    @property
    def _initialization(self):
        return os.linesep.join((
                                "",
                                "#REMOVE addons from sys.path",
                                "import os",
                                "addons_paths = %s" % self.addons_paths,
                                "addons_paths.append('%s')" % self._omelette_path,
                                "sys.path[:] = [ p for p in sys.path if not os.path.abspath(p) in addons_paths ]",
                                ""))

    def _extend_initialization_script(self, desc):
        """Remove scr path from sys path
            things tend to go wrong if there is redundancy between addons_path and PYTHONPATH,
            so we remove the parts of PYTHONPATH that are also in addons_path
        """
        initialization = desc.setdefault('initialization', "")
        initialization = os.linesep.join((
                                         initialization,
                                         self._initialization))
        desc['initialization'] = initialization

    def retrieve_addons(self):
        ServerRecipe.retrieve_addons(self)
        self.src_paths = [src for src in self.addons_paths if not src.startswith(self.openerp_dir) and os.path.exists(src)]
        self.src_paths.append(self.openerp_dir)

    def _register_test_script(self, qualified_name):
        """Register the main test script for installation.
        """
        super(Recipe, self)._register_test_script(qualified_name)
        desc = self.openerp_scripts.get(qualified_name)
        self._extend_initialization_script(desc)

    def _register_main_startup_script(self, qualified_name):
        """Register main startup script, usually ``start_openerp`` for install.
        """
        super(Recipe, self)._register_main_startup_script(qualified_name)
        desc = self.openerp_scripts.get(qualified_name)
        self._extend_initialization_script(desc)

    def _register_openerp_command(self, qualified_name):
        super(Recipe, self)._register_openerp_command(qualified_name)
        desc = self.openerp_scripts.get(qualified_name)
        self._extend_initialization_script(desc)

    def _register_upgrade_script(self, qualified_name):
        super(Recipe, self)._register_upgrade_script(qualified_name)
        desc = self.openerp_scripts.get(qualified_name)
        self._extend_initialization_script(desc)

    #def _install_interpreter(self):
    #    super(Recipe, self)._install_interpreter(self._initialization)

    def _simulate_addons_module(self):
        """Use the collective.recipe.omlette to create the right module structure
        for addons (add openrp.addons)
        The resulting package will be added to the external libs declaration to enable
        code completion and pep8 inside eclipse and removed in the generated scripts...
        """
        from collective.recipe.omelette import Recipe

        packages = []
        for path in self.src_paths:
            if path.startswith(self.openerp_dir):
                continue
            packages.append(path + " ./openerp/addons")
        options = {"packages": "\n".join(packages),
                   "recipe": "collective.recipe.omelette"}
        recipe = Recipe(self.buildout, self._omelette_name, options)
        recipe.install()

    def _generate_pydev(self):
        requirements, ws = self.egg.working_set()
        external_deps_paths = [f.location for f in ws]

        project = ET.Element("projectDescription")
        ET.SubElement(project, "name").text = self._project_name
        ET.SubElement(project, "comment")
        projects = ET.SubElement(project, "projects")
        for project_ref in self.options.get('projects', '').split():
            ET.SubElement(projects, "project").text = project_ref
        build_spec = ET.SubElement(project, "buildSpec")
        build_cmd = ET.SubElement(build_spec, "buildCommand")
        ET.SubElement(build_cmd, "name").text = "org.python.pydev.PyDevBuilder"
        ET.SubElement(build_cmd, "arguments")
        natures = ET.SubElement(project, "natures")
        ET.SubElement(natures, "nature").text = "org.python.pydev.pythonNature"
        if os.path.exists(self._fpydev_project):
            shutil.copy(self._fpydev_project, "%s.bak" % self._fpydev_project)  # make a copy of the file
        ET.ElementTree(project).write(self._fpydev_project, "UTF-8")

        # TODO: add header: "<?eclipse-pydev version="1.0"?>"
        pydev_project = ET.Element("pydev_project")
        path_property = ET.SubElement(pydev_project, "pydev_pathproperty")
        path_property.attrib['name'] = "org.python.pydev.PROJECT_SOURCE_PATH"

        for src in self.src_paths:
            ET.SubElement(path_property, "path").text = "/{name}{src}".format(
                name=self._project_name, src=src.replace(self._wd_path, ''))

        py_version = ET.SubElement(pydev_project, "pydev_property",
                                   name="org.python.pydev.PYTHON_PROJECT_VERSION")
        py_version.text = self.options['python-version']
        py_interpreter = ET.SubElement(pydev_project, "pydev_property",
                                       name="org.python.pydev.PYTHON_PROJECT_INTERPRETER")
        py_interpreter.text = self.options['python-interpreter']
        libs = ET.SubElement(pydev_project, "pydev_pathproperty",
                             name="org.python.pydev.PROJECT_EXTERNAL_SOURCE_PATH")
        for path in external_deps_paths + self.extra_paths:
            if path in self.src_paths or path.startswith(self.openerp_dir):
                continue
            ET.SubElement(libs, "path").text = path
        ET.SubElement(libs, "path").text = self._omelette_path
        if os.path.exists(self._fpydev_pydevproject):
            shutil.copy(self._fpydev_pydevproject, "%s.bak" % self._fpydev_pydevproject)  # make a copy of the file

        ET.ElementTree(pydev_project).write(self._fpydev_pydevproject, 'UTF-8')
        logger.debug("Pydev project generated " + self._fpydev_pydevproject)
        return ()

    def install(self):
        ret = super(ServerRecipe, self).install()
        self._simulate_addons_module()
        self._generate_pydev()
        return ret

    def update(self):
        """Updater"""
        self.install()
