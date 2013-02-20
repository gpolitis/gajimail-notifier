#!/usr/bin/python

import logging
import gtk
import gobject, os
import dbus
if getattr(dbus, 'version', (0,0,0)) >= (0,41,0):
    import dbus.glib

OBJ_PATH = '/org/gajim/dbus/RemoteObject'
INTERFACE = 'org.gajim.dbus.RemoteInterface'
SERVICE = 'org.gajim.dbus'
INTERVAL = 30

def relative_file(file):
    return "%s/%s" % (os.path.dirname(os.path.realpath(__file__)), file)

def update_icon():
    global count
    if count == 0:
        picture = gtk.gdk.pixbuf_new_from_file_at_size(relative_file("tray_nomail.xpm"), 16, 16)
        statusIcon.set_tooltip("No unread emails")
        statusIcon.set_from_pixbuf(picture)
    else:
        picture = gtk.gdk.pixbuf_new_from_file_at_size(relative_file("tray_unreadmail.xpm"), 16, 16)
        statusIcon.set_tooltip(("%s unread emails" % count) if count > 1 else "1 unread email")
        statusIcon.set_from_pixbuf(picture)

def poll_start():
    global count
    count = 0

    try:
        # get gajim interface
        proxy_obj = dbus.SessionBus().get_object(SERVICE, OBJ_PATH)
        gajim = dbus.Interface(proxy_obj, INTERFACE)

        # get account and associated info.
        account = gajim.list_accounts()[0]
        accountInfo = gajim.account_info(account);

        # request mail notification.
        query = '<iq type="get" to="%s"><query xmlns="google:mail:notify" /></iq>' % accountInfo['jid']
        gajim.send_xml(query, account)
    except dbus.DBusException:
        # could not connect to gajim, retry later.
        logging.debug('could not connect to gajim, retry later.')
        update_icon()
        return True

    # there's no way to intercept the server response; check count
    # variable after 3 seconds (arbitrary value).
    gobject.timeout_add(3 * 1000, poll_end)
    return False

def poll_end():
    update_icon()
    gobject.timeout_add(INTERVAL * 1000, poll_start)
    return False

def on_new_gmail(details):
    logging.debug('update unread count.')
    global count
    count = details[1][1]
    # print details

def hook_new_gmail():
    dbus.SessionBus().add_signal_receiver(on_new_gmail, 'NewGmail', INTERFACE, SERVICE, OBJ_PATH)

# logging.basicConfig(level=logging.DEBUG)

hook_new_gmail()
gobject.timeout_add(INTERVAL * 1000, poll_start)

statusIcon = gtk.StatusIcon()
picture = gtk.gdk.pixbuf_new_from_file_at_size(relative_file("tray_nomail.xpm"), 16, 16)
statusIcon.set_from_pixbuf(picture)
statusIcon.set_visible(True)

mainloop = gobject.MainLoop()
mainloop.run()

