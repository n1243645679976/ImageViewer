from collections import OrderedDict, defaultdict, deque
from tkinter import Label, Canvas, LabelFrame, Frame
from tkinter import simpledialog
from pathlib import Path
from PIL import ImageTk, Image
import multiprocessing
import threading
import tkinter as tk
import random
import yaml
import time
import io
import os

with open(r'./config.yaml') as f:
    config = yaml.safe_load(f)
w = config['window_config']['width']
h = config['window_config']['height']

start_dir = Path(config['directory_config']['init_dir'])
available_extensions = config['available_extension']
testing_keycode = False

class LFUCache:
    def __init__(self, capacity):
        self.minfreq = 0
        self.cap = capacity
        self.freq2list = defaultdict(OrderedDict)
        self.freq = {}

    def get(self, key):
        if self.cap == 0:
            return None
        if key not in self.freq:
            return None
        val = self.freq2list[self.freq[key]][key]
        del self.freq2list[self.freq[key]][key]
        if len(self.freq2list[self.minfreq]) == 0:
            self.minfreq += 1
        self.freq[key] += 1
        self.freq2list[self.freq[key]][key] = val

        return val
    def put(self, key, value):
        if self.cap == 0:
            return 
        if key not in self.freq:
            if self.cap == len(self.freq):
                k, v = self.freq2list[self.minfreq].popitem(last=False)
                del self.freq[k]
            self.freq[key] = 1
            self.minfreq = 1
        else:
            self.get(key)
        self.freq2list[self.freq[key]][key] = value
        return

            
class ImageHandler():
    def __init__(self):
        self.images_cache = LFUCache(1000) # Cache 1000 images
            
    def get_image(self, filename, window_width, window_height):
        orig_image = self.read(filename)
        resized_image, newheight, newwidth = self.resize_img(orig_image, window_width, window_height)
        image = ImageTk.PhotoImage(image=resized_image)
        return image
        
    def read(self, filename):
        orig_image = self.images_cache.get(filename)
        if orig_image == None:
            orig_image = Image.open(filename)
            self.images_cache.put(filename, orig_image)
        return orig_image
        
    def resize_img(self, orig_img, window_width, window_height):
        w, h = orig_img.width, orig_img.height
        delta = min(window_width / w, window_height / h)
        newwidth, newheight = int(w * delta), int(h * delta)
        resized_image = orig_img.resize((newwidth, newheight))
        return resized_image, newheight, newwidth
        
    
class BrowseHandler():
    def __init__(self):
        self.reset()
    
    
    def handle_keyevent(self, event, maxindexes):
        if event.keycode < 128:
            event.keycode = chr(event.keycode)
            
        if event.keycode == 'U':
            self.layer1_backward()
        elif event.keycode == 'I':
            self.layer1_forward(maxindexes)
        elif event.keycode == 'O': # end ';'
            self.layer1_last(maxindexes)
        elif event.keycode == 'Y': # home'h'
            self.layer1_first()
        elif event.keycode == '7': # 'y': to random file on layer1
            self.layer1_random(maxindexes)
        elif event.keycode == 'J':
            self.layer2_backward()
        elif event.keycode == 'K':
            self.layer2_forward(maxindexes)
        elif event.keycode == 'L': # end ','
            self.layer2_last(maxindexes)
        elif event.keycode == 'H': # home '8'
            self.layer2_first()
        elif event.keycode == '8': # 'u': to random file on subfileind
            self.layer2_random(maxindexes)
        elif event.keycode == 'M': # 'I'
            self.layer3_backward()
        elif event.keycode == 188: # 'K'
            self.layer3_forward(maxindexes)
        elif event.keycode == 190: # end ','
            self.layer3_last(maxindexes)
        elif event.keycode == 'N': # home '8'
            self.layer3_first()
            
    def set_layer_num(self, layer, num):
        if layer == 1:
            self.layer1_index = num
            self.layer2_index = 0
            self.layer3_index = 0
        elif layer == 2:
            self.layer2_index = num
            self.layer3_index = 0
        elif layer == 3:
            self.layer3_index = num
    
    def reset(self):
        self.set_layer_num(1, 0)
       
    def go_to_fileindex(self, layer, num, maxindexes):
        try:
            num = int(''.join(num)) - 1
            if layer == 1:
                self.set_layer_num(1, max(min(num, maxindexes[0] - 1), 0))
            elif layer == 2:
                self.set_layer_num(1, max(min(num, maxindexes[1] - 1), 0))
            elif layer == 3:
                self.set_layer_num(1, max(min(num, maxindexes[2] - 1), 0))
        except ValueError as e:
            pass
        
                
    def get_now_indexes(self):
        return (self.layer1_index, self.layer2_index, self.layer3_index)
        
    def layer1_forward(self, maxindexes):
        self.layer1_index = min(self.layer1_index+1, maxindexes[0]-1)
        self.layer2_index = 0
        self.layer3_index = 0
    def layer2_forward(self, maxindexes):
        self.layer2_index = min(self.layer2_index+1, maxindexes[1]-1)
        self.layer3_index = 0
    def layer3_forward(self, maxindexes):
        self.layer3_index = min(self.layer3_index+1, maxindexes[2]-1)
        
    def layer1_backward(self):
        self.layer1_index = max(self.layer1_index-1, 0)
        self.layer2_index = 0
        self.layer3_index = 0
    def layer2_backward(self):
        self.layer2_index = max(self.layer2_index-1, 0)
        self.layer3_index = 0
    def layer3_backward(self):
        self.layer3_index = max(self.layer3_index-1, 0)
        
    def layer1_first(self):
        self.layer1_index = 0
        self.layer2_index = 0
        self.layer3_index = 0
    def layer2_first(self):
        self.layer2_index = 0
        self.layer3_index = 0
    def layer3_first(self):
        self.layer3_index = 0
        
    def layer1_last(self, maxindexes):
        self.layer1_index = maxindexes[0] - 1
        self.layer2_index = 0
        self.layer3_index = 0
    def layer2_last(self, maxindexes):
        self.layer2_index = maxindexes[1] - 1
        self.layer3_index = 0
    def layer3_last(self, maxindexes):
        self.layer3_index = maxindexes[2] - 1
        
    def layer1_random(self, maxindexes):
        self.layer1_index = random.choice(range(maxindexes[0]))
        self.layer2_index = 0
        self.layer3_index = 0
    def layer2_random(self, maxindexes):
        self.layer2_index = random.choice(range(maxindexes[1]))
        self.layer3_index = 0
    def layer3_random(self, maxindexes):
        self.layer3_index = random.choice(range(maxindexes[2]))

    
class FileHandler():
    def __init__(self):
        self.sort_file_fn = [lambda x: x.stat().st_mtime, lambda x: x[1].stat().st_mtime, lambda x: x.stat().st_mtime]
        self.available_extensions = set([a.lower() for a in available_extensions])
        self.poolnode = int(config['threads'])
        self.set_root_dir(start_dir)
        
    def set_root_dir(self, dir):
        self.dir = Path(dir)
        self.filelist_layer1 = sorted(list([dir for dir in self.dir.iterdir() if dir.is_dir() or self.check_ext(dir)]), key=self.sort_file_fn[0])
        self.filelist_layer2 = [[] for _ in range(self.get_layer1_len())]
        self.reading_lock_1layer = [threading.Lock() for i in range(self.get_layer1_len())]
        self.layer1_loaded = [False for i in range(self.get_layer1_len())]
        
        self.set_layer1_dir(0)
        self.threads = [threading.Thread(target=self.set_layer1_dirs, args=(i, self.poolnode, len(self.filelist_layer1))) for i in range(self.poolnode)]
        for t in self.threads:
            t.daemon = True
            t.start()
        self.set_layer3(0, 0)
        
    def set_layer1_dirs(self, start, step, end):
        for i in range(start, end, step):
            self.set_layer1_dir(i)
        if start == 0:
            for i in range(end):
                self.set_layer1_dir(i)
            for i in range(len(self.filelist_layer1) - 1, -1, -1):
                if len(self.filelist_layer2[i]) == 0:
                    self.filelist_layer2.pop(i)
                    self.filelist_layer1.pop(i)
                    self.layer1_loaded.pop(i)
                    self.reading_lock_1layer.pop(i)
            
            
    def handle_sort_fn(self, command, layer, indexes):
        if command == 'date':
            self.set_sort_fn('d', layer, indexes[0])
        if command == 'name':
            self.set_sort_fn('n', layer, indexes[0])
            
    def set_layer3(self, layer1_index, layer2_index):
        print(':', layer1_index, layer2_index)
        if self.filelist_layer2[layer1_index][layer2_index][1].is_dir():
            self.filelist_layer3 = sorted([f for f in self.filelist_layer2[layer1_index][layer2_index][1].iterdir() if f.is_file()], key=self.sort_file_fn[2])
        else:
            self.filelist_layer3 = [self.filelist_layer2[layer1_index][layer2_index][1]]
        print(self.filelist_layer3)
        
    def set_layer1_dir(self, index):
        with self.reading_lock_1layer[index]:
            if self.layer1_loaded[index]:
                return
            if not self.layer1_loaded[index]:
                if self.filelist_layer1[index].is_dir():
                    for file in self.filelist_layer1[index].iterdir():
                        preview_file, haslayer3 = self.get_preview_file(file)
                        if preview_file != None:
                            self.filelist_layer2[index].append((preview_file, file, haslayer3))
                    
                elif self.check_ext(self.filelist_layer1[index]):
                    self.filelist_layer2[index].append((self.filelist_layer1[index], self.filelist_layer1[index], False))
            self.filelist_layer2[index].sort(key=self.sort_file_fn[1])
            self.layer1_loaded[index] = True
       
        
    def check_ext(self, file):
        return file.name.split('.')[-1].lower() in self.available_extensions
        
    def get_preview_file(self, file):
        # is_dir, then it's layer3. We find the first file to preview.
        if file.is_dir():
            for f in file.iterdir():
                if f.is_dir():
                    continue
                elif self.check_ext(f):
                    return f, True
        # is file, then return it
        else:
            if self.check_ext(file):
                return file, False
        return None, None
        
    def get_now_dir(self):
        return str(self.dir)
        
    def get_now_filename(self, indexes):
        filename = self.filelist_layer3[indexes[2]]
        return filename
        
    def get_layer1_len(self):
        return len(self.filelist_layer1)
        
    def get_layer2_len(self, layer1_index):
        self.set_layer1_dir(layer1_index)
        return len(self.filelist_layer2[layer1_index])

    def get_max_lens(self, layer1_index):
        return (len(self.filelist_layer1), len(self.filelist_layer2[layer1_index]), len(self.filelist_layer3))
        
    def set_sort_fn(self, sort_type, layer, layer1_index):
        if sort_type == 'd': # date
            if layer == 2:
                self.sort_file_fn[layer-1] = lambda x: x[1].stat().st_mtime
            else:
                self.sort_file_fn[layer-1] = lambda x: x.stat().st_mtime
        elif sort_type == 'n': # name
            if layer == 2:
                self.sort_file_fn[layer-1] = lambda x: x[1].name
            else:
                self.sort_file_fn[layer-1] = lambda x: x.name
        self.sort_file(layer, self.sort_file_fn[layer-1], layer1_index)
        
    def sort_file(self, layer, fn, layer1_index):
        if layer == 1:
            sorted_layer12 = sorted(zip(self.filelist_layer1, self.filelist_layer2), key=lambda x: fn(x[0]))
            self.filelist_layer1 = [x[0] for x in sorted_layer12]
            self.filelist_layer2 = [x[1] for x in sorted_layer12]
        elif layer == 2:
            self.filelist_layer2[layer1_index].sort(key=fn)
        elif layer == 3:
            self.filelist_layer3.sort(key=fn)
            
    def find(self, layer, query, indexes):
        if layer == 1:
            search_filelist = self.filelist_layer1
        elif layer == 2:
            search_filelist = self.filelist_layer2[indexes[0]]
        elif layer == 3:
            search_filelist = self.filelist_layer3
        query = ''.join(query)
        for i in range(len(search_filelist)):
            try:
                if search_filelist[i].name.lower().startswith(query.lower()):
                    return i
            except AttributeError:
                if search_filelist[i][1].name.lower().startswith(query.lower()):
                    return i
        return -1
            
            
class WindowHandler():
    def __init__(self):
        self.root = tk.Tk()
        self.root.title('GUI')
        self.root.geometry(f'{w}x{h}')
        self.root.bind('<KeyPress>', self.onKeyPress)
            
        self.window_width, self.window_height = w, h
        self.canvas = Label(self.root)
        self.canvas.configure(width=self.window_width, height=self.window_height)
        self.canvas.pack()
        self.browse_handler = BrowseHandler()
        self.image_handler = ImageHandler()
        self.file_handler = FileHandler()
        self.root.bind("<Configure>", self.resize_window)
        self.function_key = ''
        self.prev_keys = deque()
        self.prev_image = None
        self.set_image()
        self.set_background()
        self.set_title()
        self.root.mainloop()
        
    def onKeyPress(self, event):
        self.handle_enter(event)
        self.handle_function_key(event)
        if self.function_key == '':
            self.handle_change_root_dir(event)
            indexes = self.browse_handler.get_now_indexes()
            maxindexes = self.file_handler.get_max_lens(indexes[0])
            self.browse_handler.handle_keyevent(event, maxindexes)
            new_indexes = self.browse_handler.get_now_indexes()
            if indexes[:2] != new_indexes[:2]:
                self.file_handler.set_layer3(*new_indexes[:2])
                
        self.set_image()
        self.set_background()
        self.set_title()
            
        
    def handle_function_key(self, event):
        if event.keycode == 186: # '.': number assigning
            self.function_key += ';'
            self.prev_keys.append(';')
        elif event.keycode == 191:
            self.function_key += '/'
            self.prev_keys.append('/')
        elif event.keycode == 220:
            self.function_key += '\\'
            self.prev_keys.append('\\')
        else:
            if self.function_key != '':
                if event.keycode != 8:
                    self.prev_keys.append(chr(event.keycode))
                else:
                    if self.prev_keys:
                        self.prev_keys.pop()
    
    def handle_enter(self, event):
        if self.function_key:
            if event.keycode == 13: # enter key
                indexes = self.browse_handler.get_now_indexes()
                maxindexes = self.file_handler.get_max_lens(indexes[0])
                if self.function_key.startswith('/'):
                    self.handle_search(indexes)
                elif self.function_key.startswith(';'):
                    self.handle_set_index(indexes, maxindexes)
                elif self.function_key.startswith('\\'):
                    self.handle_command(indexes)
                new_indexes = self.browse_handler.get_now_indexes()
                if indexes[:2] != new_indexes[:2]:
                    self.file_handler.set_layer3(*new_indexes[:2])
                self.prev_keys = deque()
                self.function_key = ''
                
    def handle_search(self, indexes):
        if self.function_key.startswith('///'):
            layer = 3
            index = self.file_handler.find(3, list(self.prev_keys)[3:], indexes)
        elif self.function_key.startswith('//'):
            layer = 2
            index = self.file_handler.find(2, list(self.prev_keys)[2:], indexes)
        elif self.function_key.startswith('/'):
            layer = 1
            index = self.file_handler.find(1, list(self.prev_keys)[1:], indexes)
        if index >= 0:
            self.browse_handler.set_layer_num(layer, index)
        
    def handle_set_index(self, indexes, maxindexes):
        if self.function_key.startswith(';;;'):
            layer = 3
            self.browse_handler.go_to_fileindex(3, list(self.prev_keys)[3:], maxindexes)
        elif self.function_key.startswith(';;'):
            layer = 2
            self.browse_handler.go_to_fileindex(2, list(self.prev_keys)[2:], maxindexes)
        elif self.function_key.startswith(';'):
            layer = 1
            self.browse_handler.go_to_fileindex(1, list(self.prev_keys)[1:], maxindexes)
            
    def handle_command(self, indexes):
        if self.function_key.startswith('\\'):
            self.handle_sort_fn(indexes)
            
    def handle_sort_fn(self, indexes):
        if self.function_key.startswith('\\\\\\'):
            layer = 3
            self._handle_command(3, list(self.prev_keys)[3:], indexes)
        elif self.function_key.startswith('\\\\'):
            layer = 2
            self._handle_command(2, list(self.prev_keys)[2:], indexes)
        elif self.function_key.startswith('\\'):
            layer = 1
            self._handle_command(1, list(self.prev_keys)[1:], indexes)
        self.browse_handler.set_layer_num(layer, 0)
        new_indexes = self.browse_handler.get_now_indexes()
        self.file_handler.set_layer3(*new_indexes[:2])
        self.set_image()
        
    def _handle_command(self, layer, command, indexes):
        command = ''.join(command).lower()
        if command.startswith('sort'):
            method = command.split(' ')[1]
            self.file_handler.handle_sort_fn(method, layer, indexes)
            self.browse_handler.set_layer_num(layer, 0)
        
    def handle_change_root_dir(self, event):
        if 49 <= event.keycode <= 54:
            self.file_handler.set_root_dir(config['directory_config']['directory' + chr(event.keycode)])
            self.browse_handler.reset()
            self.set_image()
            
    def set_title(self):
        if self.function_key:
            self.root.title(''.join(self.prev_keys))
        else:
            indexes = self.browse_handler.get_now_indexes()
            maxindexes = self.file_handler.get_max_lens(indexes[0])
            if maxindexes[2] != 1:
                self.root.title(f'ImageViewer {self.file_handler.dir} [{indexes[0]+1}/{maxindexes[0]}] [{indexes[1]+1}/{maxindexes[1]}] [{indexes[2]+1}/{maxindexes[2]}]')
            else:
                self.root.title(f'ImageViewer {self.file_handler.dir} [{indexes[0]+1}/{maxindexes[0]}] [{indexes[1]+1}/{maxindexes[1]}]')
            
    def set_image(self, force=False):
        indexes = self.browse_handler.get_now_indexes()
        filename = self.file_handler.get_now_filename(indexes)
        if not force and self.prev_image == (filename, self.window_width, self.window_height):
            return
        self.prev_image = (filename, self.window_width, self.window_height)
        image = self.image_handler.get_image(filename, self.window_width, self.window_height)
        self.canvas.configure(image=image, width=self.window_width, height=self.window_height)
        self.canvas.image = image
        
    def set_background(self):
        indexes = self.browse_handler.get_now_indexes()
        maxindexes = self.file_handler.get_max_lens(indexes[0])
        if maxindexes[2] > 1:
            self.canvas['bg'] = '#dddddd'
        elif maxindexes[1] > 1:
            self.canvas['bg'] = '#ffffff'
        else:
            self.canvas['bg'] = '#000000'
                
    def resize_window(self, event):
        if (self.window_width != event.width) and (self.window_height != event.height):
            self.window_width, self.window_height = event.width,event.height
            self.set_image()
            #self.canvas.configure(width=self.window_width, height=self.window_height)
        
        
    
if __name__ == '__main__':
    tk = WindowHandler()
    