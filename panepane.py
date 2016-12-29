import sublime, sublime_plugin

class ResizeCommand(sublime_plugin.WindowCommand):
	def run(self, orientation, amount = 5):
		print("orientation: " + str(orientation))
		print("amount: " + str(amount))