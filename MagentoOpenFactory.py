#-----------------------------------------------------------------------------------
# Magento Open Factory Sublime Text Plugin
# Author: Dmitry Kovalev <dmitry.kovalev.19@gmail.com>
# Version: 1.0
# Description: Open magento factory classes: 
#				- Mage::helper('catalog')
#				- Mage::getModel('catalog/product')
#				- Mage::getResourceModel('catalog/product')
#				- Mage::getBlock('catalog/product_view')
#-----------------------------------------------------------------------------------
import sublime, sublime_plugin, re
import os.path
import glob
import xml.etree.ElementTree as ET

class Collector():
	"""Collect files"""

	def loadBase(self):
		""" Load all active modules and parse local.xml """

		self.cacheConfig = {'block' : [], 'model' : [], 'helper': [], 'resource': []}
		self.cacheRewrite = {'block' : [], 'model' : [], 'helper': [], 'resource': []}
		for folder in sublime.active_window().folders():
			modulesDir = '/app/etc/modules/'
			xmlFiles = glob.glob(folder + modulesDir + '*.xml')
			for xmlFile in xmlFiles:
				tree = ET.parse(xmlFile)
				root = tree.getroot()
				modules = root.findall("./modules/")
				for module in modules:
					active = module.find('active').text
					codepool = module.find('codePool').text
					moduleName = module.tag
					if active == 'true':
						localXmlPath = folder + '/app/code/' + codepool + '/' + self.get_file(moduleName) + '/etc/config.xml'
						if os.path.isfile(localXmlPath):
							tree = ET.parse(localXmlPath)
							root = tree.getroot()
							self.set_config(root.find('./global/blocks'), 'block')
							self.set_config(root.find('./global/models'), 'model')
							self.set_config(root.find('./global/helpers'), 'helper')

	def set_config(self, item, type):
		""" Parse xml elements and set parsed value to class variable """

		if item != None:
			for child in item.findall("./*"):
				classElement = child.find('class')
				resourceModelElement = child.find('resourceModel')
				if classElement != None:
					className = classElement.text
					classAlias = child.tag
					self.cacheConfig[type].append({classAlias : className})
				if resourceModelElement != None:
					classElement = item.find(resourceModelElement.text)
					if classElement != None:
						classElement = classElement.find('class')
						if classElement != None:
							className = classElement.text
							classAlias = child.tag
							self.cacheConfig['resource'].append({classAlias : className})
				rewrite = child.find('rewrite')
				if rewrite != None:
					self.add_rewtite(child, type)

	def add_rewtite(self, item, type):
		""" Collect rewrite aliases"""

		namspace = item.tag
		rewrite = item.find('rewrite')
		for child in rewrite.findall("./*"):
			prefix = child.tag
			classRewrite = child.text
			classAlias = namspace + '/' + prefix
			self.cacheRewrite[type].append({classAlias : classRewrite})

	def get_file_from_rewrite(self, alias, typeFactory):
		""" Get file name from rewrite"""

		for item in self.cacheRewrite[typeFactory]:
			if item.get(alias) != None:
				return item.get(alias)

	def parseSelected(self, text):
		""" Parse selected text and return class name """

		typeFactory = self.get_type_factory(text)
		if typeFactory == None:
			return

		start = text.find('(')
		finish = text.find(')')
		cutString = text[start + 2:finish - 1]
		fileName = self.get_file_from_rewrite(cutString, typeFactory)
		if fileName != None:
			return fileName
		if (cutString.find('/') != -1):
			start = cutString.find('/')
			firstCutSting = cutString[:start]
			secondCutSting = cutString[start + 1:]
			return self.get_file_from_conf(typeFactory, firstCutSting, secondCutSting)
		elif (typeFactory == 'helper'):
			return self.get_file_from_conf(typeFactory, cutString, 'data')

	def get_type_factory(self, text):
		""" Get type factory """

		typeFactory = None
		if (text.find('helper') != -1):
			typeFactory = 'helper'
		elif (text.find('ResourceModel') != -1):
			typeFactory = 'resource'
		elif (text.find('Model') != -1):
			typeFactory = 'model'
		elif (text.find('Singleton') != -1):
			typeFactory = 'model'
		elif (text.find('Block') != -1):
			typeFactory = 'block'
		return typeFactory

	def get_file_from_conf(self, typeFactory, config, prefix):
		""" Get file name from class variable """

		for item in self.cacheConfig[typeFactory]:
			if item.get(config) != None:
				return item.get(config) + '_' + prefix.title()

	def save_method_signature(self, filePath):
		""" Collect methods """

		self.cacheFunction = []
		rootDirectories = ['/app/code/core/', '/app/code/community/', '/app/code/local/']
		for folder in sublime.active_window().folders():
			for root in rootDirectories:
				if os.path.isfile(folder+root+filePath):
					file_lines = open(folder+root+filePath, 'rU')
					for line in file_lines:
						if "function" in line:
							matches = re.search('function\s*(\w+)\s*\((.*)\)', line)
							if matches != None:
								self.cacheFunction.append(matches.group(1) + '(' + matches.group(2) + ')')
								

	def get_text(self):
		""" Get text """

		sels = self.view.sel()
		if (len(sels) == 1):
			text = self.view.substr(sels[0])
			if (len(text) == 0):
				text = self.view.substr(self.view.line(sublime.Region(self.view.sel()[0].begin())))
		return text

	def get_file(self, text):
		""" Get file by magento class """

		return text.strip().replace('_', '/')

	def get_php_file(self, text):
		""" Get php file by magento class """

		return self.get_file(text) + '.php'


class MagentoOpenFactory(Collector, sublime_plugin.TextCommand):
	""" Open factory class """

	def run(self, edit):
		self.loadBase()
		text = self.get_text()
		fileName = self.parseSelected(text)
		if fileName != None:
			self.open(self.get_php_file(fileName))

	def open(self, filePath):
		""" Open file """

		rootDirectories = ['/app/code/core/', '/app/code/community/', '/app/code/local/']
		for folder in sublime.active_window().folders():
			for root in rootDirectories:
				if os.path.isfile(folder+root+filePath):
					sublime.active_window().open_file(folder+root+filePath)
					return

class MagentoSelectFactoryMethods(Collector, sublime_plugin.TextCommand):
	""" Select factory methods """

	def run(self, edit):
		self.loadBase()
		text = self.get_text()
		fileName = self.parseSelected(text)
		if fileName == None:
			return
		self.save_method_signature(self.get_php_file(fileName))

		sublime.active_window().show_quick_panel(self.cacheFunction, self.apply_method)


	def apply_method(self, ind):
		""" Apply selected method """

		if ind == -1:
			return
		line = self.view.sel()[0].begin()
		insert = self.cacheFunction[ind]
		args = {'line' : line, 'insert' : insert}
		sublime.active_window().run_command('magento_insert_method', args)

class MagentoInsertMethod(sublime_plugin.TextCommand):

	def run(self, edit, line, insert):
		sublime.active_window().active_view().insert(edit, line, insert)

		