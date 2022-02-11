import sublime
import sublime_plugin
import os
import threading
import time
import re

REG_FUNC_NAME=".* \*?(\S+)\s*\("
REG_VAR_NAME=".* \*?(\S+)\s*\="
TYPES_CODES=[
	{"type": ["short int"], "code": "%hd"},
	{"type": ["unsigned short int"], "code": "%hu"},
	{"type": ["unsigned int","uint32_t"], "code": "%u"},
	{"type": ["signed int","int","int32_t"], "code": "%d"},
	{"type": ["long int"], "code": "%ld"},
	{"type": ["unsigned long int"], "code": "%lu"},
	{"type": ["long long int"], "code": "%lld"},
	{"type": ["unsigned long long int"], "code": "%llu"},
	{"type": ["signed char","unsigned char","char"], "code": "%c"},
	{"type": ["float"], "code": "%f"},
	{"type": ["double"], "code": "%lf"},
	{"type": ["long double"], "code": "%Lf"},
	{"type": ["size_t"], "code": "%zu"},
	{"type": ["ssize_t"], "code": "%zd"},
]

class ExampleCommand(sublime_plugin.TextCommand):

	def get_current_line(self):
		(my_line,row) = self.view.rowcol(self.view.sel()[0].begin())
		return my_line

	def get_cur_filename(self):
		return self.view.window().active_view().file_name()

	def get_func_bound_lines(self, file_name, my_line):
		stream = os.popen('cscope -R -L -1 ".*" '+file_name+' |grep "'+file_name+'"|grep -v "#"')
		output = stream.read()

		all_defs=output.split("\n")
		sel_f=all_defs[len(all_defs) - 2].split(" ")

		for l in range(len(all_defs)):
			cur_def=all_defs[l].split(" ")
			if(len(cur_def)>1):
				cur_line=cur_def[2]

				if(int(cur_line) > my_line):
					sel_f=(all_defs[l-1].split(" "))
					p = re.compile(REG_FUNC_NAME)
					t = p.match(" ".join(sel_f))
					func_name = None
					if t:
						func_name=t.group(1)

					return [
						(int(sel_f[2]) - 1),
						int(cur_line),
						func_name
					]

		return None

	def get_selected_text(self):
		sel = self.view.sel()[0]
		selected = self.view.substr(sel)
		return selected

	def get_local_var_decl(self, file_name, var_name, func_name):
		if(not len(var_name) or var_name is None):
			print("var_name empty")
			return None

		stream = os.popen('cscope -R -L -0 ".*" '+file_name+' |grep "'+var_name+'"|grep -v "#"')
		output = stream.read()

		all_defs=output.split("\n")
		sel_f=all_defs[len(all_defs) - 2].split(" ")

		for l in range(len(all_defs)):
			cur_def=all_defs[l].split(" ")
			if(cur_def[1] == func_name):
				return " ".join(cur_def[3:])
		return None

	def create_printf_var(self, line, var_name):
		
		vardef= line.split("=")[0]

		if "*" in vardef:return None
		if "[" in vardef:return None
		if "," in vardef:return None

		vardef=vardef.split(" ")

		try:
			vardef.remove("const")
			vardef.remove("static")
		except:
			pass

		vardef.remove(var_name)
		vardef.remove('')

		for t in TYPES_CODES:
			for u in t["type"]:
				if(u == " ".join(vardef)):
					return "printf(\""+var_name+"="+t["code"]+"\", "+var_name+");\n\n"

	def run(self, edit):
		file_name=self.get_cur_filename()
		my_line = self.get_current_line()

		j=self.get_local_var_decl(
			self.get_cur_filename(),
			self.get_selected_text(),
			self.get_func_bound_lines(file_name, my_line)[2],
		)

		gen_printf=self.create_printf_var(j, self.get_selected_text())
		point = self.view.text_point(my_line + 1, 0)
		self.view.insert(edit, point, gen_printf)

