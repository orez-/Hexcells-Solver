import time

import AppKit as appkit
import pyscreenshot
import Quartz as quartz


def _get_active_window():
    workspace = appkit.NSWorkspace.sharedWorkspace()
    activeApps = workspace.runningApplications()
    for app in activeApps:
        name = app.localizedName()
        if name and name.startswith('Hexcells'):  # TODO: this is a stopgap
        # if app.isActive():
            options = quartz.kCGWindowListOptionOnScreenOnly
            windowList = quartz.CGWindowListCopyWindowInfo(options, quartz.kCGNullWindowID)
            for window in windowList:
                if window['kCGWindowOwnerName'] == app.localizedName():
                    return window


def grab_game_screen():
    window = None
    while True:
        window = _get_active_window()
        name = window['kCGWindowOwnerName']
        if name.startswith('Hexcells'):
            break
        print("Please make Hexcells the active window ({!r}).".format(name))
        time.sleep(3)
        continue

    top_bar_height = 20  # TODO: less magic pls
    dims = window['kCGWindowBounds']
    bbox = (
        int(dims['X']),
        int(dims['Y']) + top_bar_height,
        int(dims['Width']),
        int(dims['Height']) - top_bar_height,
    )
    return pyscreenshot.grab(
        bbox=bbox,
        # importing Quartz before trying to screenshot causes a segfault without this flag. ᖍ(シ)ᖌ
        childprocess=False,
    ), (bbox[0], bbox[1])


if __name__ == '__main__':
    time.sleep(2)
    grab_game_screen().show()
