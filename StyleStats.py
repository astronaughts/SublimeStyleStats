import sublime
import sublime_plugin
import subprocess
import os
import json
import collections
import re

RESULTVIEW_NAME = "StyleStats!"
SETTINGS_FILE = "StyleStats.sublime-settings"

TITLE_WIDTH = 33
CONTENT_WIDTH = 44
HEADER = "┌" + ("─" * TITLE_WIDTH) + "┬" + ("─" * CONTENT_WIDTH) + "┐\n"
SPACER = "├" + ("─" * TITLE_WIDTH) + "┼" + ("─" * CONTENT_WIDTH) + "┤\n"
FOOTER = "└" + ("─" * TITLE_WIDTH) + "┴" + ("─" * CONTENT_WIDTH) + "┘\n"


def padTo(value, pad_to, pad_string=" "):
    string = str(value)
    return "%s%s" % (string, pad_string * (pad_to - len(string)))


def createLine(title, content):
    return "│" + padTo(title, TITLE_WIDTH) + "│" + padTo(content, CONTENT_WIDTH) + "│\n"


class SssResultCommand(sublime_plugin.TextCommand):

    def run(self, edit, data):
        window = self.view.window()
        result_view = None

        for view in window.views():
            if view.name() == RESULTVIEW_NAME:
                result_view = view

        if result_view is None:
            result_view = window.new_file()
            result_view.set_name(RESULTVIEW_NAME)

        content = HEADER
        for title, value in data.items():
            title = re.sub('([a-z0-9])([A-Z])', r'\1 \2', title).title()
            if title == "Properties Count":
                content = content + createLine(title, "%s: %s" % (value[0]["property"], value[0]["count"]))
                for child in value[1:]:
                    content = content + createLine("", "%s: %s" % (child["property"], child["count"]))
            elif type(value) == list:
                content = content + createLine(title, value[0])
                for child in value[1:]:
                    content = content + createLine("", child)
            else:
                content = content + createLine(title, value)

            content = content + SPACER
        content = content + FOOTER

        result_view.set_read_only(False)
        result_view.set_scratch(True)
        result_view.replace(edit, sublime.Region(0, result_view.size()), content)
        result_view.set_read_only(True)
        window.focus_view(result_view)


class SssAnalysisCommand(sublime_plugin.WindowCommand):

    def run(self, path):
        settings = sublime.load_settings(SETTINGS_FILE)
        bin_path = settings.get("bin_path")

        def get_json_to_result(url):
            command = [bin_path, "-t", "json", url]
            shell = os.name == "nt"
            output = subprocess.check_output(
                command,
                shell=shell,
            )
            try:
                data = json.loads(
                    output.decode(encoding="utf-8"),
                    object_pairs_hook=collections.OrderedDict
                )
                self.window.run_command("sss_result", {"data": data})
            except:
                sublime.error_message("Error: Please specify a CSS file. - " + url)

        sublime.set_timeout(lambda: get_json_to_result(path))


class SssSpecificAnalysisCommand(sublime_plugin.WindowCommand):

    def run(self):
        self.window.show_input_panel("StyleStats - Path or URL", "", self.on_done, None, None)

    def on_done(self, url):
        self.window.run_command("sss_analysis", {"path": url})


class SssCurrentFileAnalysisCommand(sublime_plugin.WindowCommand):

    def run(self):
        view = self.window.active_view()
        self.window.run_command("sss_analysis", {"path": view.file_name()})
