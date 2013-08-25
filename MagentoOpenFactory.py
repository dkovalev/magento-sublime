#-----------------------------------------------------------------------------------
# Magento Open Factory Sublime Text Plugin
# Author: Dmitry Kovalev <dmitry.kovalev.19@gmail.com>
# Version: 1.0
# Description: Open magento factory classes: 
#				- Mage::helper('catalog')
#				- Mage::getModel('catalog/product')
#				- Mage::getBlock('catalog/product_view')
#-----------------------------------------------------------------------------------
import sublime, sublime_plugin
import os.path
import glob
import xml.etree.ElementTree as ET

class MagentoOpenFactory(sublime_plugin.TextCommand):
	def run(self, edit):
		self.cacheConfig = {'block' : [], 'model' : [], 'helper': []}
		self.loadBase()
		sels = self.view.sel()
		if (len(sels) == 1):
			text = self.view.substr(sels[0])
			if (len(text)):
				fileName = self.parseSels(text)
				self.open(self.get_php_file(fileName))

	def loadBase(self):
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
						tree = ET.parse(localXmlPath)
						root = tree.getroot()
						self.set_config(root.find('./global/blocks'), 'block')
						self.set_config(root.find('./global/models'), 'model')
						self.set_config(root.find('./global/helpers'), 'helper')

	def parseSels(self, text):
		if (text.find('helper') != -1):
			typeFactory = 'helper'
		elif (text.find('Model') != -1):
			typeFactory = 'model'
		elif (text.find('Block') != -1):
			typeFactory = 'block'

		start = text.find('(')
		finish = text.find(')')
		cutString = text[start + 2:finish - 1]
		if (cutString.find('/') != -1):
			start = cutString.find('/')
			firstCutSting = cutString[:start]
			secondCutSting = cutString[start + 1:]
			return self.get_file_from_conf(typeFactory, firstCutSting, secondCutSting)
		elif (typeFactory == 'helper'):
			return self.get_file_from_conf(typeFactory, cutString, 'data')

	def get_file_from_conf(self, typeFactory, config, prefix):
		for item in self.cacheConfig[typeFactory]:
				if item.get(config) != None:
					return item.get(config) + '_' + prefix.title()

	def open(self, filePath):
		rootDirectories = ['/app/code/core/', '/app/code/community/', '/app/code/local/']

		for folder in sublime.active_window().folders():
			for root in rootDirectories:
				if os.path.isfile(folder+root+filePath):
					sublime.active_window().open_file(folder+root+filePath)
					return

	def set_config(self, item, type):
		if item != None:
			for child in item.findall("./*"):
				classElement = child.find('class')
				if classElement != None:
					className = classElement.text
					classAlias = child.tag
					self.cacheConfig[type].append({classAlias : className})

	def get_file(self, text):
		return text.strip().replace('_', '/')

	def get_php_file(self, text):
		return self.get_file(text) + '.php'