import sublime, sublime_plugin
import os
import re
import functools

PACKAGE_NAME = "Actionscript 3"
PACKAGE_PATH = os.path.join(sublime.packages_path(), PACKAGE_NAME)

SRC_ROOT_FOLDER = 'src'

def get_files_in_folder(folder, extensions):
    """ Get the files in a given folder.
        Returns a list of fully qualified file name strings.

    """
    file_paths = []
    for (dirpath, dirs, files) in os.walk(folder, followlinks=True):
        file_paths.extend(
            [ os.path.join(dirpath, f) for f in files 
                                       if f.endswith(extensions) ])
    return file_paths

def split_path_to_file(path):
    while path is not None:
        split = os.path.split(path)
        if split[1]:
            path = split[0]
            yield split[1]
        else:
            path = None
            yield split[0]


def add_text(view, point, text):
    """ Adds the text to the given view at the given point """
    edit = view.begin_edit()
    view.insert(edit, point, text)
    view.end_edit(edit)

def create_src_file(window, package, file_name):
    """ Creates a new Actionscript 3 source file.
        Using the given window, will attempt to infer where
        to place the file based on the package name.

        Returns a handle to the file.

    """
    src_root = find_src_root(window)
    package_path = os.path.join(*package.split("."))
    directory = os.path.join(src_root, package_path)
    full_file_name = file_name + ".as"
    full_path = os.path.join(directory, full_file_name)

    if (os.path.isfile(full_path)):
        return None # TODO proper errors

    if not os.path.exists(directory):
        os.makedirs(directory)

    return open(os.path.join(directory, full_file_name), 'w')

def find_src_root(window):
    if window.active_view() is not None:
        return find_src_root_from_view(window.active_view())
    else:
        return find_src_root_from_window(window)

def find_src_root_from_view(view):
    file_path = view.file_name()
    folder_path = os.path.split(file_path)[0]
    folder = os.path.split(folder_path)[1]
    while folder is not None:
        if folder == SRC_ROOT_FOLDER:
            return folder_path
        folder_path,folder = os.path.split(folder_path)
    return None

def find_src_root_from_window(window):
    for folder in window.folders():
        for (path, dirs, files) in os.walk(folder, followlinks=True):
            for dirname in dirs:
                if dirname == SRC_ROOT_FOLDER:
                    return os.path.join(path, dirname)
    return None


def request_new_as3_file(window, callback, type):
    """ Ask the user to input a package name, and a 'type' name.
        Creates a new AS3 file and calls callback with the new file,
        the inputted package name and 'type' name.

    """
    window.show_input_panel(
        "New %s package:" % type, "", 
        lambda p: window.show_input_panel(
                "New %s name:" % type, "", 
                lambda t: callback(p, t), 
                None, None
            ), 
        None, None
    )

def get_class_name(view):
    """ Attempts to find the class name of a given view.
        Returns either a string or None.

    """
    regions = view.find_by_selector("entity.name.class.actionscript.3")
    return view.substr(regions[0]) if regions else None

def get_methods(view):
    """ Attempts to find all the class methods in the given view.

        Returns a list of found methods.  Methods include both the
        function signature and the block of code.

    """
    regions = view.find_by_selector("meta.method.actionscript.3")
    return [view.substr(region) for region in regions]


class As3ImportCommand(sublime_plugin.TextCommand):
    """ as3_import allows the user to search their project for classes to 
        import, adding the appropriate import statement to the file.

    """

    def run(self, edit):
        class_list = []
        for folder in self.view.window().folders():
            class_list.extend(get_files_in_folder(folder, '.as'))
        class_list = self.prettify_class_list(class_list)
        self.view.window().show_quick_panel(
            class_list, 
            lambda picked: self.on_select_class(class_list, picked)
        )

    def on_select_class(self, class_list, i):
        if i > -1:
            self.try_add_import(self.view, class_list[i])

    def prettify_class_list(self, class_list):
        return filter(None, [self.format_to_import(c) for c in class_list])

    def format_to_import(self, classpath):
        folders = []
        for folder in split_path_to_file(classpath):
            if folder == SRC_ROOT_FOLDER:
                break
            else:
                folders.insert(0, folder)
        
        formatted = ".".join(folders)
        formatted = formatted[:-3] #remove .as extension
        return formatted if "." in formatted else ""

    def try_add_import(self, view, import_path):
        previous_imports = view.find_by_selector("meta.import.actionscript.3")
        for previous_import in reversed(previous_imports):
            point = previous_import.b + 1 # since the selector doesn't capture ;
            if self.check_valid_import_area(view, point):
                previous_import_path = view.substr(previous_import)
                whitespace = previous_import_path.split("import")[0]
                self.insert_import(view, point, whitespace, import_path)
                return

        # Couldn't find any valid areas underneath a previous import, so try 
        # to insert below the package declaration instead
        pkg_name = view.find_by_selector("meta.package_name.actionscript.3")
        if len(pkg_name) > 0:
            point = pkg_name[0].b
            self.insert_import(view, point, "\t", import_path)

    
    def check_valid_import_area(self, view, point):
        if view.score_selector(point, "meta.package.actionscript.3"):
            return True
        elif view.score_selector(point, "meta.cdata.actionscript.3"):
            return True
        else:
            return False

    def insert_import(self, view, point, whitespace, path):
        # TODO Figure out how/if we can use sublimes automatic identation
        text = "\n%simport %s;" % (whitespace, path)
        add_text(view, point, text)


class As3NewClassCommand(sublime_plugin.WindowCommand):
    """ as3_new_class sets up the boilerplate code when writing a new class.

    """

    def run(self):
        request_new_as3_file(self.window, self.fill_class, "class")

    def fill_class(self, package_name, class_name):
        new_class = create_src_file(self.window, package_name, class_name)
        f = open(os.path.join(PACKAGE_PATH, "data", "new_class.template"))
        try:
            text = f.read()
            text = text.replace("${package_name}", package_name)
            text = text.replace("${class_name}", class_name)
            new_class.write(text)
        finally:
            new_class.close()
            f.close()

        self.window.open_file(new_class.name)


class As3NewInterfaceCommand(sublime_plugin.WindowCommand):
    """ as3_new_class sets up the boilerplate code when writing a new 
        interface. 

    """

    def run(self):
        request_new_as3_file(self.window, self.fill_interface, "interface")

    def fill_interface(self, package_name, interface_name):
        interface = create_src_file(self.window, package_name, interface_name)
        f = open(os.path.join(PACKAGE_PATH, "data", "new_interface.template"))
        try:
            text = f.read()
            text = text.replace("${package_name}", package_name)
            text = text.replace("${interface_name}", interface_name)
            text = text.replace("${functions}", "")
            interface.write(text)
        finally:
            interface.close()
            f.close()

        self.window.open_file(interface.name)


class As3NewEventCommand(sublime_plugin.WindowCommand):
    """ as3_new_event sets up the boilerplate code when writing a new event. 

    """

    def run(self):
        request_new_as3_file(self.window, self.fill_event, "event")

    def fill_event(self, package_name, event_name):
        event = create_src_file(self.window, package_name, event_name)
        f = open(os.path.join(PACKAGE_PATH, "data", "new_event.template"))
        try:
            text = f.read()
            text = text.replace("${package_name}", package_name)
            text = text.replace("${event_name}", event_name)
            event.write(text)
        finally:
            event.close()
            f.close()

        self.window.open_file(event.name)


class As3ExtractInterfaceCommand(sublime_plugin.TextCommand):
    """ as3_extract_interface sets up a new interface based on the public 
        functions in the currently open class.
        
    """

    def run(self, edit):
        request_new_as3_file(self.view.window(), self.request_file_callback, 
                             "interface")

    def request_file_callback(self, package_name, interface_name):
        # self.insert_implements(interface_name) # TODO
        methods = [method.split("{")[0] for method in get_methods(self.view)]
        functions = self.get_functions(methods)
        self.fill_interface(package_name, interface_name, functions)

    def insert_implements(self, interface_name):
        # TODO
        find = self.view.find_by_selector(
            "meta.class_declaration.actionscript.3"
        )
        insert_point = find[0].b - 1
        add_text(self.view, insert_point, "implements %s " % interface_name)

    def get_functions(self, methods):
        valid_methods = [ method.strip() for method in methods 
                                         if self.is_public(method) 
                                         and not self.is_constructor(method) 
                                         and not self.is_static(method) ]
        return [method.split(" function ")[1] for method in valid_methods]

    def fill_interface(self, package_name, interface_name, functions):
        functions = [("\t\tfunction %s;" % f) for f in functions]
        interface = create_src_file(
            self.view.window(), package_name, interface_name
        )
        f = open(os.path.join(PACKAGE_PATH, "data", "new_interface.template"))
        try:
            text = f.read()
            text = text.replace("${package_name}", package_name)
            text = text.replace("${interface_name}", interface_name)
            text = text.replace("${functions}", "\n\n".join(functions))
            interface.write(text)
        finally:
            interface.close()
            f.close()

        self.view.window().open_file(interface.name)

    def is_public(self, function):
        found = re.search("\s+public\s+", function)
        return True if found else False

    def is_static(self, function):
        found = re.search("\s+static\s+", function)
        return True if found else False

    def is_constructor(self, function):
        class_name = get_class_name(self.view)
        if class_name:
            found = re.search("\s+%s\s*\(" % class_name , function)
        else:
            return False
        return True if found else False