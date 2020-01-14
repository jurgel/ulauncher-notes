import uuid
import json
import gi
import os

gi.require_version('Gdk', '3.0')
gi.require_version('Gtk', '3.0')

from gi.repository import Gdk, Gtk, GObject
from os.path import expanduser
from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent, ItemEnterEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.HideWindowAction import HideWindowAction
from ulauncher.api.shared.action.ExtensionCustomAction import ExtensionCustomAction

class NotesExtension(Extension):
    def __init__(self):
        super(NotesExtension, self).__init__()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())
        self.subscribe(ItemEnterEvent, ItemEnterEventListener())

home = expanduser("~")
notesFilePath = '%s/.notes' % home 
if not os.path.isfile(notesFilePath):
    f = open(notesFilePath, 'w')
    f.close()

def saveNote(note):
    note['id'] = str(uuid.uuid4())
    del note['mode']
    f = open(notesFilePath, 'a')
    f.write('%s\n' % json.dumps(note))
    f.close()

def updateNote(newNote):
    notes = getNotes()
    f = open(notesFilePath, 'w')
    for note in notes:
        if note['id'] == newNote['id']:
            note['label'] = newNote['new_label']
        f.write('%s\n' % json.dumps(note))
    f.close()

def deleteNote(deleteNote):
    notes = getNotes()
    f = open(notesFilePath, 'w')
    for note in notes:
        if note['id'] != deleteNote['id']:
            f.write('%s\n' % json.dumps(note))
    f.close()

def copyToClipboard(note):
    clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
    clipboard.set_text(note['data'], -1)
    clipboard.store()
    GObject.timeout_add(1, Gtk.main_quit)
    Gtk.main()

def getNotes():
    notes = []
    f = open(notesFilePath, 'r')
    lines = f.read().split('\n')
    f.close()

    for data in lines:
        if data == '' or data == None:
            continue
        note = json.loads(data)
        notes.append(note)
    return notes


class KeywordQueryEventListener(EventListener):
    def on_event(self, event, extension):
        if event.get_keyword() == 'n':
            resNotes = []
            f = open(notesFilePath, 'r')
            lines = f.read().split('\n')
            f.close()
            
            notes = getNotes()            	
            for note in notes:
                note['mode'] = ''

                if event.get_argument() == 'delete' or event.get_argument() == 'del' or event.get_argument() == 'd':
                    note['mode'] = 'deleteNote'
                elif event.get_argument() == 'copy' or event.get_argument() == 'c':
                    note['mode'] = 'copyToClipboard'
                elif event.get_argument() is None or event.get_argument().strip() == '':
                    note['mode'] = 'copyToClipboard'
                else:
                    note['mode'] = 'updateNote'
                    note['new_label'] = event.get_argument()

                resNotes.append(ExtensionResultItem(icon='note.png',
                                         name=note['data'],
                                         description=note.get('label', ''),
                                         on_enter=ExtensionCustomAction(note, keep_app_open=True)))
            return RenderResultListAction(resNotes)

        if event.get_keyword() == 'nn':
            note = {}
            note['data'] = event.get_argument()
            note['mode'] = 'addNewNote'
            return RenderResultListAction([ExtensionResultItem(icon='note.png',
                                             name='New Note:',
                                             description=note['data'],
                                             on_enter=ExtensionCustomAction(note, keep_app_open=True))])


class ItemEnterEventListener(EventListener):
    def on_event(self, event, extension):
        note = event.get_data()
        if note['mode'] == 'addNewNote':
            saveNote(note)
        elif note['mode'] == 'deleteNote':
            deleteNote(note)
        elif note['mode'] == 'copyToClipboard':
            copyToClipboard(note)
        elif note['mode'] == 'updateNote':
            updateNote(note)

        return HideWindowAction()

if __name__ == '__main__':
    NotesExtension().run()

