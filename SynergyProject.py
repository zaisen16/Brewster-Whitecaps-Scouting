###########################
### Preparing dataframe ###
###########################

import pandas  # Import the pandas library for handling dataframes

# Import Trackman file/filepath
TMfile = pandas.read_csv('~/Downloads/2024 IU Trackman Files/20240312-Vanderbilt-1_unverified.csv')  # Load Trackman CSV data
# Import Synergy output file/filepath
SynergyFile = pandas.read_csv("~/Downloads/Thompson/Export.csv")  # Load Synergy CSV data

### Create a key to connect the pitches/rows in each dataframe

# Key for Synergy file

# Convert the "Inning" column from strings like "T1" to just the number "1"
SynergyFile['Inning'] = SynergyFile['Inning'].str.extract('(\d+)')

# Concatenate relevant columns to create a unique "Key" for identifying rows
SynergyFile['Key'] = (
    SynergyFile['Pitcher'] + "_" +
    SynergyFile['#'].astype(int).astype(str)
)

# Key for Trackman file

# Clean NA rows
TMfile = TMfile.dropna(subset=['Pitcher'])

# Create pitch count column
TMfile['PitchCount'] = TMfile.groupby("Pitcher").cumcount() + 1

# Adjust the "Date" column format to match Synergy's date format
# TMfile['Date'] = pandas.to_datetime(TMfile['Date'], format='%Y-%m-%d').dt.strftime('%m/%d/%Y')

# Define a function to reformat names into the "Last, F." format
def reformat_name(full_name):
    parts = full_name.split(", ")
    if len(parts) == 2:
        last_name = parts[0]
        first_name = parts[1].split(" ")[0]  # Extract the first name
        return f"{last_name}, {first_name[0]}."  # Format as "Last, F."
    return full_name  # Return unchanged if unexpected format

# Apply the name reformatting function to the "Pitcher" and "Batter" columns
TMfile['Pitcher'] = TMfile['Pitcher'].apply(reformat_name)
TMfile['Batter'] = TMfile['Batter'].apply(reformat_name)

# Concatenate relevant columns to create a unique "Key" for Trackman rows
TMfile['Key'] = (
    TMfile['Pitcher'].astype(str) + "_" +
    TMfile['PitchCount'].astype(int).astype(str)
)

# Optional debugging: Print column data types to identify import issues
# print(TMfile[['Date', 'Pitcher', 'Batter', 'Inning', 'Balls', 'Strikes']].dtypes)

### Merge the two files

# Perform an inner join on the "Key" column to combine the datasets
merged_df = pandas.merge(TMfile, SynergyFile, on='Key', how='inner')

# Select only the necessary columns for the final merged dataframe
merged_df = merged_df[['Key', 'Pitcher_x', 'Hitter', 'Balls', 'Strikes', 'TaggedPitchType', 'PitchCall', 'RelSpeed', 'InducedVertBreak', 'HorzBreak', 'SpinRate', 'Inning_x', 'Outs_x', 'PitchCount', '#']]

# Change NaN values to 0
merged_df = merged_df.fillna(0)

# Validate that the merged dataframe has the same number of rows as the Synergy file
# If not, some pitches may have been excluded, requiring manual checks
len(merged_df)
len(SynergyFile)
len(SynergyFile) == len(merged_df)  # Check if all rows match

##############################
### Editing the videos now ###
##############################

import os  # Import os for handling file paths and directories
from os import path  # Import path module for file path operations

# List all video files in the specified directory
clips = os.listdir("/Users/zacharyaisen/Downloads/Thompson/video/")
paths = [os.path.join("/Users/zacharyaisen/Downloads/Thompson/video/", i) for i in clips]

# List of all video file paths
paths

# Retrieve a list of video numbers from the merged dataframe
video_nums = list(merged_df['#_x'])

import moviepy  # Import moviepy for video editing

# Iterate over the video file paths
for i in paths:
    # Skip files that are not video files
    if not i.lower().endswith((".mp4")):
        continue

    # Extract the file name and row number
    filepath = i
    filepath_split = filepath.split("/")
    filename = filepath_split[-1].split(".")
    row_num = int(filename[0]) - 1  # Adjust file numbering to match dataframe index

    # Retrieve data points for overlaying on the video
    PitchType = merged_df.loc[row_num, 'TaggedPitchType']
    Balls = int(merged_df.loc[row_num, 'Balls'])
    Strikes = int(merged_df.loc[row_num, 'Strikes'])
    Inning = int(merged_df.loc[row_num, 'Inning_x'])
    Outs = int(merged_df.loc[row_num, 'Outs_x'])
    Pitcher = merged_df.loc[row_num, 'Pitcher_x']
    Batter = merged_df.loc[row_num, 'Hitter']
    result = merged_df.loc[row_num, 'PitchCall']
    velo = round(merged_df.loc[row_num, 'RelSpeed'], 1)
    vert = round(merged_df.loc[row_num, 'InducedVertBreak'], 1)
    horz = round(merged_df.loc[row_num, 'HorzBreak'], 1)
    Spin = int(merged_df.loc[row_num, 'SpinRate'])

    # Create text strings for overlaying onto the video
    text = "Pitch Type: " + PitchType + "\n" + "Result: " + result + "\n" + "Velo: " + str(velo) + "\n" + "iVB: " + str(vert) + "\n" + "HB: " + str(horz) + "\n" + "Spin Rate: " + str(Spin)
    text2 = "Inning: " + str(Inning) + "\n" + "Pitcher: " + Pitcher + "\n" + "Batter: " + Batter + "\n" + "Count: " + str(Balls) + "-" + str(Strikes) + "\n" + "Outs: " + str(Outs)

    ### Using moviepy to overlay text onto the video
    from moviepy.editor import *  # Import necessary components for editing

    # Load the video file without audio
    raw_video = VideoFileClip(filepath).without_audio()

    # Create text clips for overlay, setting duration and position
    txt_clip = TextClip(text, fontsize=20, font="Roboto-Bold", color='white', align='West', bg_color='black').set_opacity(0.85).set_pos(('left', 'top')).set_duration(raw_video.duration)
    txt2_clip = TextClip(text2, fontsize=20, font="Roboto-Bold", color='white', align='East', bg_color='black').set_opacity(0.85).set_pos(('right', 'top')).set_duration(raw_video.duration)

    # Combine the raw video with text overlays
    video = CompositeVideoClip([raw_video, txt_clip, txt2_clip])

    # Set the output file name for the final edited video
    finalvideo_filename = filename[0] + "_edited.mp4"

    # Export the final video as an MP4 file
    video.write_videofile(finalvideo_filename, codec="libx264", preset="ultrafast")


###################################
### Concatenate videos together ###
###################################

# Lists all videos in the folder
video_files = [f for f in os.listdir("/Users/zacharyaisen/Downloads/Thompson") if f.endswith("_edited.mp4")]

# Sort videos numerically
video_files_sorted = sorted(video_files, key=lambda x: int(x.split("_")[0]))

# Load video clips
clips = [VideoFileClip(os.path.join("/Users/zacharyaisen/Downloads/Thompson", f)) for f in video_files_sorted]

# Concatenate the videos
final_video = concatenate_videoclips(clips, method="compose")  # method="compose" ensures compatibility

# Export the final combined video
final_video.write_videofile("final_video.mp4", codec="libx264", preset="ultrafast")
