#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pafy
import tkinter
import threading
import time
import codecs
import sys
import os
from random import shuffle
from os import chdir, getcwd
from vlc import Instance, State
from tkinter import messagebox, font
from requests import get
from bs4 import BeautifulSoup

class SmolPlayer:
    def __init__(self, window):
        fnt = ('Ariel', 11)
        for favorite in ['Quicksand Medium', 'DejaVu Sans', 'Dingbats', 'Droid Sans Fallback']:
            if favorite in font.families():
                fnt = (favorite, 11)
                break
        directory = getcwd()
        chdir(directory)
        self.ticker = 0
        self.paused = False
        self.nowPlaying = ''
        self.songPosition = 0
        self.player = ''
        self.volume = 50
        self.run = True
        self.threadLock = threading.Lock()
        self.window = window
        self.window.title('SmolPlayer')
        self.window.configure(background='#323740')
        self.width, self.height = self.window.winfo_screenwidth(), self.window.winfo_screenheight()
        self.window.geometry('%dx%d+%d+%d' % (790, 590, self.width // 2 - 400, self.height // 2 - 340))
        self.window.resizable(False, False)

        playImage = tkinter.PhotoImage(file='assets/play.png')
        pauseImage = tkinter.PhotoImage(file='assets/pause.png')
        skipImage = tkinter.PhotoImage(file='assets/skip.png')
        shuffleImage = tkinter.PhotoImage(file='assets/shuffle.png')

        self.pauseButton = tkinter.Button(self.window, image=pauseImage, bg='#323740', relief='flat',
                                          command=self.pause)
        # tkinter.Button(self.window, text = 'Clear', width=10, command = self.clear).place(x=380,y=5)

        self.playButton = tkinter.Button(self.window, image=playImage, bg='#323740', relief='flat', command=self.start)
        self.playButton.place(x=300, y=10)
        self.skipButton = tkinter.Button(self.window, image=skipImage, bg='#323740', relief='flat', command=self.skip)
        self.skipButton.place(x=360, y=10)
        self.shuffleButton = tkinter.Button(self.window, image=shuffleImage, bg='#323740', relief='flat',
                                            command=self.shuffle)
        self.shuffleButton.place(x=420, y=10)

        tkinter.Button(self.window, text='Add', bg='blue', width=5, command=self.add, font=fnt).place(x=685, y=120)
        self.nextButton = tkinter.Button(self.window, text='Next', width=5, command=self.up_next, font=fnt)
        self.nextButton.place(x=685, y=150)
        self.deleteButton = tkinter.Button(self.window, text='Delete', width=5, command=self.delete_song, font=fnt)
        self.deleteButton.place(x=685, y=180)
        self.volumeScale = tkinter.Scale(self.window, from_=100, to=0, orient='vertical', bg='#323740', fg='white',
                                         borderwidth=0, highlightbackground='#323740', length=242,
                                         command=self.set_volume)
        self.volumeScale.place(x=690, y=240)
        self.volumeScale.set(self.volume)
        self.musicScrubber = tkinter.Scale(self.window, from_=0.0, to=1.0, resolution=0.0001, orient='horizontal',
                                           bg='#323740', width=5, fg='#323740', borderwidth=0,
                                           highlightbackground='#323740', length=718)
        self.musicScrubber.place(x=38, y=85)
        self.queueBox = tkinter.Listbox(self.window, width=65, height=20, font=fnt)
        self.queueBox.place(x=40, y=150)
        self.urlEntry = tkinter.Entry(self.window, width=65, font=fnt)
        self.urlEntry.place(x=40, y=120)
        self.nowPlayingLabel = tkinter.Label(self.window, text='Now Playing:', bg='#323740', fg='white',
                                             font=fnt)
        self.nowPlayingLabel.place(x=37, y=80)
        self.durationLabel = tkinter.Label(self.window, text='/ 00:00:00', bg='#323740', fg='pink', font=fnt)
        self.durationLabel.place(x=680, y=80)
        self.timeLabel = tkinter.Label(self.window, text='00:00:00', bg='#323740', fg='pink', font=fnt)
        self.timeLabel.place(x=615, y=80)

        self.musicScrubber.bind('<ButtonRelease-1>', lambda x: self.set_scrubber(self.musicScrubber.get()))
        self.urlEntry.bind('<Return>', self.add)
        self.urlEntry.bind('<ButtonRelease-3>', self.paste)
        self.queueBox.bind('<Delete>', self.delete_song)

        self.refresh()
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.window.mainloop()

    def start(self):
        if self.paused:
            self.paused = False
            self.player.set_pause(0)
            self.playButton.config(state='disabled')
            self.playButton.place_forget()
            self.pauseButton.place(x=300, y=10)
        else:
            t1 = threading.Thread(target=self.play)
            t1.daemon = True
            t1.start()

    def play(self):
        with open('urllist.txt', 'r') as f:
            url = f.readline().strip()
        if url:
            try:
                self.threadLock.acquire()
                ytdl_opts = {'source_address': '0.0.0.0', 'format': 'bestaudio/best'}
                video = pafy.new(url, ydl_opts=ytdl_opts)
                best = video.getbest()
                playurl = best.url
                vInstance = Instance('--novideo')
                self.player = vInstance.media_player_new()
                media = vInstance.media_new(playurl)
                self.player.set_media(media)
                self.player.play()
                self.playButton.place_forget()
                self.pauseButton.place(x=300, y=10)
                self.player.audio_set_volume(int(self.volume))
                self.nowPlaying = video.title
                self.durationLabel.config(text=f'/ {video.duration}')
                h, m, s = video.duration.split(':')
                duration = int(h) * 3600 + int(m) * 60 + int(s)
                ticker = 1 / duration
                try:
                    self.nowPlayingLabel.config(text=f'Now Playing: {self.nowPlaying}')
                    with open('nowPlaying.txt', 'w', encoding='utf-8') as f:
                        f.write(self.nowPlaying + '   ')
                except:
                    self.nowPlaying = self.nowPlaying.encode('unicode_escape')
                    self.nowPlayingLabel.config(text=f'Now Playing: {self.nowPlaying}')
                    with open('nowPlaying.txt', 'w', encoding='utf-8') as f:
                        f.write(str(self.nowPlaying) + '   ')
                self.playButton.config(state='disabled')
                self.threadLock.release()
                self.shuffleButton.config(state='disabled')
                self.deleteButton.config(state='disabled')
                self.nextButton.config(state='disabled')
                for i in range(3):
                    self.songPosition += ticker
                    self.musicScrubber.set(self.songPosition)
                    self.get_time()
                    time.sleep(1)
                if self.player.get_state() == State.Ended:
                    self.nowPlayingLabel.config(text='RETRYING CONNECTION')
                    self.play()
                else:
                    self.update()
                self.shuffleButton.config(state='normal')
                self.deleteButton.config(state='normal')
                self.nextButton.config(state='normal')
                self.songPosition = ticker * 3
                self.musicScrubber.set(ticker * 3)
                while self.player.get_state() == State.Playing or self.player.get_state() == State.Paused:
                    if not self.paused:
                        self.songPosition += ticker
                        self.musicScrubber.set(self.songPosition)
                        self.get_time()
                        time.sleep(1)
                    if not self.run:
                        self.player.stop()
                        sys.exit()
                self.songPosition = 0
                self.musicScrubber.set(0)
                self.player.stop()
                self.play()
            except Exception as error:
                if self.threadLock.locked():
                    self.threadLock.release()
                messagebox.showwarning(title='Warning', message=error)
                self.update()
                self.play()
        else:
            self.playButton.config(state='normal')
            self.pauseButton.place_forget()
            self.playButton.place(x=300, y=10)
            self.nowPlayingLabel.config(text='Now Playing:')
            self.durationLabel.config(text='/ 00:00:00')
            self.timeLabel.config(text='00:00:00')
            with open('nowPlaying.txt', 'w', encoding='utf-8') as f:
                f.write('No songs playing. Donate to have your song played on stream.   ')

    def get_time(self):
        vtime = self.player.get_time() // 1000
        vtime = time.strftime('%H:%M:%S', time.gmtime(vtime))
        self.timeLabel.config(text=vtime)

    def shuffle(self):
        with open('songlist.txt', 'r', encoding='utf-8') as f:
            songs = f.readlines()
        with open('urllist.txt', 'r', encoding='utf-8') as f:
            urls = f.readlines()
        combined = list(zip(songs, urls))
        if not combined:
            return
        shuffle(combined)
        songs[:], urls[:] = zip(*combined)
        with open('songlist.txt', 'w', encoding='utf-8') as f:
            for song in songs:
                f.write(song)
        with open('urllist.txt', 'w') as f:
            for url in urls:
                f.write(url)
        self.refresh()

    def pause(self):
        if self.player.get_state() == State.Playing:
            self.player.set_pause(1)
            self.paused = True
            self.playButton.config(state='normal')
            self.pauseButton.place_forget()
            self.playButton.place(x=300, y=10)

    def set_volume(self, amount):
        if self.player:
            self.player.audio_set_volume(int(amount))
            self.volume = amount

    def set_scrubber(self, amount):
        try:
            self.player.set_position(amount)
            self.songPosition = amount
        except:
            self.musicScrubber.set(0)

    def skip(self):
        if self.player:
            self.player.stop()
        self.paused = False

    def add(self, event=None):
        url = self.urlEntry.get()
        self.urlEntry.delete(0, 'end')
        if url.startswith('https://www.youtube.com/') or url.startswith('https://youtu.be') or url.startswith(
                'https://m.youtube.com'):
            if 'playlist' in url:
                playlist = get(url).text
                soup = BeautifulSoup(playlist, 'lxml')
                for vid in soup.find_all('a', {'dir': 'ltr'}):
                    if '/watch' in vid['href']:
                        url = ('https://www.youtube.com' + vid['href']).split('&list')[0]
                        with open('urllist.txt', 'a') as f:
                            f.write(f'{url}\n')
                        with open('songlist.txt', 'a', encoding='utf-8') as f:
                            f.write(f'{vid.string.strip()}\n')
                self.refresh()
            else:
                url = self.check(url)
                webpage = get(url).text
                soup = BeautifulSoup(webpage, 'lxml')
                title = soup.title.string
                with open('urllist.txt', 'a') as f:
                    f.write(f'{url}\n')
                with open('songlist.txt', 'a', encoding='utf-8') as f:
                    f.write(f'{title}\n')
                self.refresh()
        else:
            query = url.replace(' ', '+')
            video = get(f'https://www.youtube.com/results?search_query={query}').text
            soup = BeautifulSoup(video, 'lxml')
            results = soup.find_all('a', {'class': 'yt-uix-tile-link'})
            if len(results) == 0:
                messagebox.showinfo("Couldn't Find Song",
                                    "SmolPlayer could not find a song matching your query. Try revising your search.")
            else:
                for vid in results:
                    if '/watch' in vid['href']:
                        url = 'https://www.youtube.com' + vid['href']
                        songTitle = vid['title']
                        url = self.check(url)
                        with open("urllist.txt", "a") as f:
                            f.write(f'{url}\n')
                        with open("songlist.txt", "a", encoding='utf-8') as f:
                            f.write(f'{songTitle}\n')
                        self.refresh()
                        break

    def up_next(self):
        selected = self.queueBox.curselection()
        if len(selected) == 0:
            return
        index = int(selected[0])
        with open('songlist.txt', 'r', encoding='utf-8') as f:
            songs = f.readlines()
        with open('urllist.txt', 'r', encoding='utf-8') as f:
            urls = f.readlines()
        songs.insert(0, songs[index])
        songs.pop(index + 1)
        urls.insert(0, urls[index])
        urls.pop(index + 1)
        with open('songlist.txt', 'w', encoding='utf-8') as f:
            for song in songs:
                f.write(song)
        with open('urllist.txt', 'w') as f:
            for url in urls:
                f.write(url)
        self.refresh()

    def update(self):
        with open("urllist.txt", "r") as f:
            data = f.readlines()
        with open("urllist.txt", "w") as f:
            f.writelines(data[1:])
        with codecs.open("songlist.txt", "r", encoding='utf-8') as f:
            data = f.readlines()
        with codecs.open("songlist.txt", "w", encoding='utf-8') as f:
            f.writelines(data[1:])
        self.refresh()

    def refresh(self):
        with open("songlist.txt", "r", encoding='utf-8') as f:
            songlist = f.readlines()
            self.queueBox.delete(0, 'end')
            for line in songlist:
                try:
                    self.queueBox.insert('end', line)
                except:
                    song = line.encode('unicode_escape')
                    self.queueBox.insert('end', f'{song}\n')

    def check(self, url):
        characters = len(url)
        if characters <= 43:
            return url
        else:
            messagebox.showwarning("SmolPlayer",
                                   "Song from playlist. If you wanted to add a playlist please use the playlist page url instead.")
            url = url[:43]
            return url

    def delete_song(self, event=None):
        selected = self.queueBox.curselection()
        if len(selected) == 0:
            return
        self.queueBox.delete(selected)
        selected = int(selected[0])
        with open("songlist.txt", "r", encoding='utf-8') as f:
            data = f.readlines()
            data.pop(selected)
            data = ''.join(data)
        with open("songlist.txt", "w", encoding='utf-8') as f:
            f.write(data)
        with open("urllist.txt", "r") as f:
            data = f.readlines()
            data.pop(selected)
            data = ''.join(data)
        with open("urllist.txt", "w") as f:
            f.write(data)

    def paste(self, event=None):
        try:
            self.clipboard = self.window.clipboard_get()
            self.urlEntry.insert(0, self.clipboard)
            self.window.clipboard_clear()
            self.add()
        except:
            pass

    # This function is not in use right now
    def clear(self):
        self.queueBox.delete(0, 'end')
        with open("songlist.txt", "w", encoding="utf-8") as f:
            f.write('')
        with open("urllist.txt", "w") as f:
            f.write('')

    def stopped(self):
        while not self._stop_event.is_set():
            continue

    def on_closing(self):
        try:
            self.run = False
            self.player.set_pause(0)
            self.window.destroy()
        except:
            self.window.destroy()


if __name__ == '__main__':
    for filename in ['songlist.txt', 'urllist.txt']:
        if not os.path.exists(filename):
            open(filename, 'w').close()
    mainWindow = tkinter.Tk()
    SmolPlayer(mainWindow)
    mainWindow.quit()
