#!/usr/bin/env python3
import re
import random

from tkinter import *
from tkinter.ttk import *

# Import Tk standard dialogs
from tkinter import filedialog

WORD_REGEX = re.compile(r"\*([a-z]+)\*")


class WordMap:
    """Loads a word map from a file of the following line format:
    
    PART_OF_SPEECH COLOR WORD1 [WORD2 [...]]
    
    PART_OF_SPEECH must be a word containing only lowercase letters
    COLOR must be a Tk color string (e.g., "red" or "#ffcccc")
    WORDx can be any whitespace-delimited word
    
    No WORDs should be duplicated, anywhere...
    
    Also keeps track of how many times a given word has been "used"
    in a game of madlib.  Can notify interested objects when a word's
    count changes.
    """
    def __init__(self, filename):
        self._observers = []
        
        # Load the word map from the file
        self._wordmap = {}
        self._wordcount = {}
        with open(filename) as fd:
            for line in fd:
                fields = line.split()
                part, color, words = fields[0], fields[1], fields[2:]
                self._wordmap[part] = (color, words)
                
                for word in words:
                    self._wordcount[word] = 0
    
    def get_word_list(self):
        """Returns a list of (word, part, count) tuples, sorted by word."""
        wordlist = []
        for part, (color, words) in self._wordmap.items():
            for word in words:
                wordlist.append((word, part, self._wordcount[word]))
        wordlist.sort()
        return wordlist
    
    def get_part_names(self):
        """Return a sorted list of part-of-speech names."""
        parts = [part for part in self._wordmap]
        parts.sort()
        return parts
    
    def get_part_color(self, name):
        """Return the color of a part of speech."""
        return self._wordmap[name][0]
    
    def register_count_observer(self, callback):
        """Register a callable to be invoked when a word's count changes.
        
        Callable must take 2 parameters: word (str), and new count (int)
        """
        self._observers.append(callback)
    
    def pick_word(self, part):
        """Randomly pick a word from a given part of speech.
        
        Updates the word count.
        """
        # Pick word, update count
        word = random.choice(self._wordmap[part][1])
        self._wordcount[word] += 1
        
        # Notify "observers"
        for observer in self._observers:
            observer(word, self._wordcount[word])
        
        return word


class WordTable(Frame):
    """Create a table view of words, their parts of speech, and use count."""
    def __init__(self, parent):
        super().__init__(parent)
        self._items = []    # Hack to keep track of currently-inserted words
        
        # Build a tree view and populate it with the words
        # (We don't use this as a tree per se, just as a multi-column list)
        # (notice that the first column is implicit; we list only the 2nd and 3rd
        # columns here; also, we don't want the user to be able to select anything)
        self._tv = Treeview(self, columns=["part", "count"], selectmode="none")
        
        # Set column properties
        self._tv.column("#0", width=200, stretch=False) # Column #0 means the "primary" (leftmost) column
        self._tv.column("part", width=350, stretch=True)
        self._tv.column("count", width=200, stretch=False)
        
        # Set column captions
        self._tv.heading("#0", text="From")
        self._tv.heading("part", text="Subject")
        self._tv.heading("count", text="Date")
        
        # Make a scrollbar for us, too
        scrolly = Scrollbar(self, orient=VERTICAL, command=self._tv.yview)
        self._tv["yscrollcommand"] = scrolly.set
        
        # Pack 'em in...
        scrolly.pack(side=RIGHT, fill=Y)
        self._tv.pack(expand=YES, fill=BOTH)
    
    def load_wordmap(self, wordmap: WordMap):
        # Clear out tree
        for item in self._items:
            self._tv.delete(item)
        
        # Add new items from the word map
        self._items = []
        for word, part, num in wordmap.get_word_list():
            self._items.append(word)
            self._tv.insert('',     # No parent (top-level item in "tree")
                END,                # Insert at END of list
                word,               # Use the word itself as the item ID
                text=word,          # Display the word itself in column #0
                values=(part, num)) # Put the part of speech and count in the other columns
        
        # Register for updates to the counts
        wordmap.register_count_observer(self.update_word_count)
        
    def update_word_count(self, word, new_count):
        """Record the use of one of our words."""
        part, _ = self._tv.item(word, "values")
        self._tv.item(word, values=(part, new_count))


class MadlibText(Frame):
    """A compound widget for playing MadLib.
    
    Must have a WordMap object and a text "story" to work;
    both of these are provided after object creation via
    the "load_wordmap" and "load_story" methods.
    """
    def __init__(self, parent):
        super().__init__(parent)
        
        # No wordmap yet
        self._wordmap = None
        
        # Wire up text/scrollbar widgets
        self._text = Text(self, wrap="word")
        scrolly = Scrollbar(self, orient=VERTICAL, command=self._text.yview)
        self._text['yscrollcommand'] = scrolly.set
        
        # Pack them into the containing frame
        scrolly.pack(side=RIGHT, fill=Y)
        self._text.pack(expand=YES, fill=BOTH)
    
    def load_wordmap(self, wordmap: WordMap):
        # Delete all "tags" associated with the text widget
        self._text.tag_delete(self._text.tag_names())
        
        self._wordmap = wordmap
        
        # Create new tags for each part of speech
        for part in wordmap.get_part_names():
            # Colors
            self._text.tag_configure(part, background=wordmap.get_part_color(part))
            self._text.tag_configure(part + "_rep", foreground=wordmap.get_part_color(part))
            
            # Events
            self._text.tag_bind(part, "<Button-1>", self._click_tag)
        
        # Highlight the story.
        self._highlight()
    
    def _click_tag(self, e):
        # Figure out exactly which tag-span was clicked
        part = self._text.tag_names(CURRENT)[0]
        begin, end = self._text.tag_prevrange(part, CURRENT)
        
        # Replace that word, tagging it as "<part>_rep" to indicate it was replaced
        replacement = self._wordmap.pick_word(part)
        self._text.delete(begin, end)
        self._text.insert(begin, replacement, (part + "_rep",))
    
    def load_story(self, story: str):
        # Clear out all text
        self._text.delete("1.0", END)
        
        # Update the text view
        self._text.insert(END, story)
        
        # Do we have a wordmap?  If so, highlight the story
        if self._wordmap:
            self._highlight()
    
    def _highlight(self):
        if not self._wordmap:
            raise Exception("Must have a word map!")
        
        # Find and tag each part-of-speech placeholder appropriately
        for match in WORD_REGEX.finditer(self._text.get('1.0', END)):
            start, end = match.span()
            index1 = "1.0 + {0} chars".format(start)
            index2 = "1.0 + {0} chars".format(end)
            self._text.tag_add(match.group(1), index1, index2)


class MadlibApp:
    def __init__(self):
        root = Tk()
        self._root = root
        root.title("tkMadLib")
        self._style = Style(self._root)
        self._style.theme_use("clam")
        
        # Resizable panes, side-by-side
        panes = PanedWindow(root, orient=VERTICAL)
        
        # Left side: a word table and a set of buttons
        frame = Frame(panes)
        
        panel = Frame(frame)
        btn_newMsg = Button(panel, text="New Message", command=self._load_words)
        btn_newMsg.pack(side=LEFT, padx=5, pady=5)
        btn_reply = Button(panel, text="Reply", command=self._load_words)
        btn_reply.pack(side=LEFT, padx=5, pady=5)
        btn_delete = Button(panel, text="Delete", command=self._load_words)
        btn_delete.pack(side=LEFT, padx=5, pady=5)
        btn_getMail = Button(panel, text="Get Mail", command=self._load_words)
        btn_getMail.pack(side=LEFT, padx=5, pady=5)
        btn_config = Button(panel, text="Configure", command=self._load_story)
        btn_config.pack(side=LEFT, padx=5, pady=5)
        panel.pack(side=TOP, fill=X)
        
        self._table = WordTable(frame)
        self._table.pack(expand=YES, fill=BOTH)

        # Right side: the scrolling text view
        self._text = MadlibText(panes)

        # Complete the layout
        panes.add(frame)
        panes.add(self._text)    
        panes.pack(expand=YES, fill=BOTH)

##My command definitions
    
    def _load_words(self):
        wordfile = filedialog.askopenfilename()
        if wordfile:
            wordmap = WordMap(wordfile)
            self._table.load_wordmap(wordmap)
            self._text.load_wordmap(wordmap)
    
    def _load_story(self):
        storyfile = filedialog.askopenfilename()
        if storyfile:
            with open(storyfile) as fd:
                story = fd.read()
            self._text.load_story(story)
    
    def run(self):
        """Run the application to termination."""
        self._root.mainloop()

if __name__ == "__main__":
    MadlibApp().run()
