from tkinter import *
import pygame
from tkinter import filedialog
import time
import mutagen
from mutagen.mp3 import MP3
import tkinter.ttk as ttk
import os
from tinytag import TinyTag
import sqlite3
import webbrowser

root = Tk()
root.title('Sebs_Musicbowl')
root.geometry("500x500")

# initiate Pygame Mixer (Audio interpreter)
pygame.mixer.init( )

#create and connect to playlist
verbindung_playlist = sqlite3.connect("playlist.db")
playlistzeiger = verbindung_playlist.cursor()

sql_anweisung = """
CREATE TABLE IF NOT EXISTS playlist (
Titel VARCHAR(100), 
Songpath VARCHAR(500),
Number int
);"""

#delete all previous entrys
playlistzeiger.execute("DELETE FROM playlist")
#execute the instructions
verbindung_playlist.commit()

global song_quantity
song_quantity = 0

#Grab song lenght time info
def play_time():
    #Check for dobble timing
    if stopped:
        return
    #Grab current Song Elapsed Time
    current_time =pygame.mixer.music.get_pos() / 1000

    # convert to time format
    converted_current_time = time.strftime('%H:%M:%S', time.gmtime(current_time))

    #get active song from playlisttable
    global current_song_number
    song = get_songpath_from_playlisttable(current_song_number)
    #get Song Lenght with Mutagen
    song_mut = MP3(song)
    #Get song Lenghth
    global song_length
    song_length = song_mut.info.length
    #Convert to Time Format
    converted_song_length = time.strftime('%H:%M:%S', time.gmtime(song_length))

    # Increas current time by one second
    current_time +=1

    if int(my_slider.get()) == int(song_length):
        #Output time to status bar
        status_bar.config(text=f'Time Elepsed: {converted_song_length}  ')

    elif paused:
        pass

    elif int(my_slider.get()) == int(current_time):
        # slider hasn't been moved
        #Update slider to position
        slider_position = int(song_length)
        my_slider.config(to=slider_position, value=int(current_time))
   
    else:
        # slider has moved
        #Update slider to position
        slider_position = int(song_length)
        my_slider.config(to=slider_position, value=int(my_slider.get()))
        
        # convert to time format
        converted_current_time = time.strftime('%H:%M:%S', time.gmtime(int(my_slider.get())))

        #Output time to status bar
        status_bar.config(text=f'Time Elepsed: {converted_current_time} of {converted_song_length}  ')

        #Move this thing along by one second
        next_time = int(my_slider.get()) + 1
        my_slider.config(value = next_time)

    #update Time
    status_bar.after(1000, play_time)


# Add Song Funktion
def add_song():
    # get file path
    songpath = filedialog.askopenfilename(initialdir='audio/', title="Choos a Song", filetypes=(("mp3 Files", "*.mp3"), ))
    
    # get file name
    tag = TinyTag.get(songpath)
    songtitle = tag.title
    print("Tag Title")
    print(songtitle)

    global song_quantity
    song_quantity = song_quantity + 1
    song_number = song_quantity
    
    #add song to playlisttable
    playlistzeiger.execute("""
                INSERT INTO playlist 
                       VALUES (?,?,?)
               """, 
              (songtitle, songpath, song_number)
              )
    verbindung_playlist.commit()
    
    song_box.insert("end", songtitle)
    
    

#Add many Songs to Playlist
def add_many_songs():
    songs = filedialog.askopenfilenames(initialdir='audio/', title="Choos a Song", filetypes=(("mp3 Files", "*.mp3"), ))
    # Loop thru song list and replace directory indo and mp3
    for songpath in songs:
        # get file name
        tag = TinyTag.get(songpath)
        songtitle = tag.title
        print("Tag Title")
        print(songtitle)

        global song_quantity
        song_quantity = song_quantity + 1
        song_number = song_quantity
    
        #add song to playlisttable
        playlistzeiger.execute("""
                INSERT INTO playlist 
                       VALUES (?,?,?)
               """, 
              (songtitle, songpath, song_number)
              )
        verbindung_playlist.commit()
    
        # Add Song to listbox
        song_box.insert("end", songtitle)
        

#play selected Song
def play():
    stop()
    #set stopped variable to False so song can play
    global stopped
    stopped = False

    #get active song title
    songtitle = song_box.get(ACTIVE)
    #get songpath from playlisttable
    #search for active song in playlisttable
    playlistzeiger.execute("SELECT Number FROM playlist Where Titel = ?", (songtitle,))
    current_song_number_list = playlistzeiger.fetchall() 
    #convert from list to string + correction   
    global current_song_number
    current_song_number = str(current_song_number_list)
    current_song_number = current_song_number.replace("[(", "")
    current_song_number = current_song_number.replace(",)]", "")
    #current_song_number = int(current_song_number)
    print("Current_song_number:")
    print(current_song_number)

    #get songpath from playlisttable
    songpath = get_songpath_from_playlisttable(current_song_number)

    #play the loaded song
    pygame.mixer.music.load(songpath)
    pygame.mixer.music.play(loops=0)

    # Call the play_time funktion to get song lenght
    play_time()

    

#Stop playing current Song
global stopped
stopped = False

def stop():
     #Reset Slider and status bar
     status_bar.config(text='')
     my_slider.config(value=0)
     #Stop Song from Playing
     pygame.mixer.music.stop()
     song_box.selection_clear(ACTIVE)

     #Clear the Status Bar
     status_bar.config(text='')

     #Set Stop Variable to true
     global stopped
     stopped = True

#Create Global Pause Variable
global paused
paused = False

#pause unpause current Song
def pause(is_paused):
    global paused
    paused = is_paused

    if paused:
        #unpause
        pygame.mixer.music.unpause()
        paused = False
    else:
        #pause
        pygame.mixer.music.pause()
        paused = True
    
#play the next Song in the Playlist
def next_song():
    #Reset Slider and status bar
    status_bar.config(text='')
    my_slider.config(value=0)
    #get the current song tuple number
    global current_song_number
    # Add one to the current song number
    current_song_number = int(current_song_number)
    current_song_number = current_song_number + 1
    #Grab song title from playlist
    song = get_songpath_from_playlisttable(current_song_number)
    if song == "[]":
        next_song()
    else:
        #load and play song
        pygame.mixer.music.load(song)
        pygame.mixer.music.play(loops=0)

        #clear aktive bar in playlist listbox
        song_box.select_clear(0,END)

        #correct for songbox
        current_song_number2 = current_song_number - 1
        #activate new song bar
        song_box.activate(current_song_number2)

        #set Active bar to next song
        song_box.selection_set(current_song_number2, last=None)

#Play previous song in Playlist
def previous_song():
    #Reset Slider and status bar
    status_bar.config(text='')
    my_slider.config(value=0)
    #get the current song tuple number
    global current_song_number
    current_song_number = int(current_song_number)
    # Add one to the current song number
    current_song_number = current_song_number - 1
    #Grab song title from playlist
    song = get_songpath_from_playlisttable(current_song_number)
    #load and play song
    pygame.mixer.music.load(song)
    pygame.mixer.music.play(loops=0)

    #clear aktive bar in playlist listbox
    song_box.select_clear(0,END)

    #correct for songbox
    current_song_number2 = current_song_number - 1
    #activate new song bar
    song_box.activate(current_song_number2)

    #set Active bar to next song
    song_box.selection_set(current_song_number2, last=None)


#Delete  a song
def delete_song():
    #get active song title
    songtitle = song_box.get(ACTIVE)
    #get songpath from playlisttable
    #search for active song in playlisttable
    playlistzeiger.execute("DELETE FROM playlist Where Titel = ?", (songtitle,))
    verbindung_playlist.commit()
    #delete selected song
    song_box.delete(ANCHOR)
    #stop music if it's playing
    pygame.mixer.music.stop()

#Delete all songs form Playlist
def delete_all_songs():
    stop()
    #delete all songs in playlist
    song_box.delete(0, END)
    playlistzeiger.execute("DELETE FROM playlist")
    verbindung_playlist.commit()
    global song_quantity
    song_quantity = 0
    #stop music if it's playing
    pygame.mixer.music.stop()


#get songpath from active song
def get_songpath_from_playlisttable(current_song_number):
    #get active song number
    number = current_song_number
    #get songpath from playlisttable
    #search for active song in playlisttable
    playlistzeiger.execute("SELECT Songpath FROM playlist Where Number = ?", (number,))
    songpathlist = playlistzeiger.fetchall() 
    #convert from list to string + correction   
    songpath = str(songpathlist)
    replacements = [
        ("[('", ""),
        ("',)]", ""),
        (f'[("', ""),
        (f'",)]', "")
    ]
    for old, new in replacements:
        songpath = songpath.replace(old, new)
    
    return songpath


#Create slider funktion
def slide(x):
    global current_song_number
    song = get_songpath_from_playlisttable(current_song_number)
    pygame.mixer.music.load(song)
    pygame.mixer.music.play(loops=0, start=int(my_slider.get()))


#create Volume Funktion
def volume(x):
    pygame.mixer.music.set_volume(volume_slider.get())


def display_original_project():
    webbrowser.open('https://github.com/Bastler-Seb/Sebs_Musicbowl')


# Create Master Frame
master_frame = Frame(root)
master_frame.pack(pady=20)

# Create Playlist box
song_box = Listbox(master_frame, bg="black", fg="green", width=60, selectbackground="gray", selectforeground="black")
song_box.grid(row=0, column=0)

# Create Playlist Array
playlist = []

# Create Player Control Buttons Images
back_btn_img = PhotoImage(file='Button Images/Back_Button.png')
forward_btn_img = PhotoImage(file='Button Images/forward_Button.png')
play_btn_img = PhotoImage(file='Button Images/Play_Button.png')
pause_btn_img = PhotoImage(file='Button Images/Pause_Button.png')
stop_btn_img = PhotoImage(file='Button Images/Stop_Button.png')

# Create Player Control Frame
controls_frame = Frame(master_frame)
controls_frame.grid(row=1, column=0, pady=20)

#Create Volume label Frame
volume_frame = LabelFrame(master_frame, text="Volume")
volume_frame.grid(row=0, column=1, padx=20)

# Create Player Control Buttons
back_button = Button(controls_frame, image=back_btn_img, borderwidth=0, command=previous_song)
forward_btn = Button(controls_frame, image=forward_btn_img, borderwidth=0, command=next_song)
play_btn = Button(controls_frame, image=play_btn_img, borderwidth=0, command=play)
pause_btn = Button(controls_frame, image=pause_btn_img, borderwidth=0, command=lambda: pause(paused))
stop_btn = Button(controls_frame, image=stop_btn_img, borderwidth=0, command=stop)

back_button.grid(row=0, column=0, padx=10)
forward_btn.grid(row=0, column=1, padx=10)
play_btn.grid(row=0, column=2, padx=10)
pause_btn.grid(row=0, column=3, padx=10)
stop_btn.grid(row=0, column=4, padx=10)

# Create Menue
my_menu = Menu(root)
root.config(menu=my_menu)

# Add "Add Song Menu"
add_song_menu = Menu(my_menu)
my_menu.add_cascade(label="Add Songs", menu=add_song_menu)
add_song_menu.add_command(label="Add One Song to Playlist", command=add_song)

# Add "Add many Songs Menu"
add_song_menu.add_command(label="Add many Songs to Playlist", command=add_many_songs)

#Create Delete Song Menu
remove_song_menu = Menu(my_menu)
my_menu.add_cascade(label="Remove Songs", menu=remove_song_menu)
remove_song_menu.add_command(label="Delete a song from Playlist", command=delete_song)
remove_song_menu.add_command(label="Delete All songs from Playlist", command=delete_all_songs)

#Create Info Menu
info_menu =  Menu(my_menu)
my_menu.add_cascade(label="Info", menu=info_menu)
info_menu.add_command(label="Original Project", command=display_original_project)

#Create Status Bar
status_bar = Label(root, text='', bd=1, relief=GROOVE, anchor=E)
status_bar.pack(fill=X, side=BOTTOM, ipady=2)

#Create Music Position Slider
my_slider = ttk.Scale(master_frame, from_=0, to=100, orient=HORIZONTAL, value=0, command=slide, length=360)
my_slider.grid(row=2, column=0, pady=10)

# Create Volume Slider
volume_slider = ttk.Scale(volume_frame, from_=1, to=0, orient=VERTICAL, value=1, command=volume, length=125)
volume_slider.pack(pady=10)



root.mainloop()
