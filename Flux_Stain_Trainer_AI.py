import matplotlib.pyplot as plt  # Import matplotlib module for plt
from tkinter import filedialog  # Import filedialog module from tkinter for filedialog
from sklearn import metrics  # Import metrics module from sklearn for metrics
from tqdm import tqdm  # Import tqdm module for tqdm
import os  # Import os module for os
import cv2  # Import cv2 module for cv2
import numpy as np  # Import numpy module for np
import tensorflow as tf  # Import tensorflow module for tf
from sklearn.model_selection import train_test_split  # Import train_test_split module from sklearn for train_test_split
from keras.models import Sequential  # Import Sequential module from keras for Sequential
from keras.layers import Dense, Dropout, Flatten, Conv2D, MaxPooling2D  # Import Dense, Dropout, Flatten, Conv2D, MaxPooling2D modules from keras for Sequential
from keras.optimizers import Adam  # Import Adam module from keras for Adam
from keras.regularizers import l2  # Import l2 for adding regularization
from keras.callbacks import EarlyStopping  # Import EarlyStopping
from keras.preprocessing.image import ImageDataGenerator  # Import ImageDataGenerator for data augmentation

import tkinter as tk  # Import tkinter module for tk

# Define global variables for input and output folders
with_flux_folder = ""
without_flux_folder = ""
output_folder = "output"
model_file = "Flux_Stain_Model.h5"

# Create a function to browse for input folders and update label
def browse_input_folders(folder_type, label_widget):
    global with_flux_folder, without_flux_folder
    folder = filedialog.askdirectory(title=f"Select {folder_type} Folder")
    if folder:
        label_widget.config(text=folder)
        if folder_type == "With Flux":
            with_flux_folder = folder
        elif folder_type == "Without Flux":
            without_flux_folder = folder

# Create a function to browse for the output folder and update label
def browse_output_folder(label_widget):
    global output_folder
    output_folder = filedialog.askdirectory(title="Select Output Folder")
    if output_folder:
        label_widget.config(text=output_folder)

# Create a function to preprocess images
def preprocess_image(image):
    resized_image = cv2.resize(image, (100, 100))
    normalized_image = resized_image / 255.0
    return normalized_image

# Create a function to apply a specific filter to the image
def apply_filter(image, filter_type):

        # Check image dtype and convert if necessary
    if image.dtype == 'float64':  # or np.float64
        image = (image * 255).astype('uint8')

    # Convert to grayscale
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    if filter_type == 'blur':
        filtered_image = cv2.blur(image, (5, 5))
    elif filter_type == 'sharpen':
        kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
        filtered_image = cv2.filter2D(image, -1, kernel)
    elif filter_type == 'edge_detection':
        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray_image, 100, 200)
        filtered_image = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
    else:
        raise ValueError("Invalid filter type")
    
    return filtered_image

# Create a function to enhance the contrast of the image
def enhance_contrast(image):
    # Check if the image is single-channel (grayscale)
    if len(image.shape) == 3:
        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray_image = image

    # Ensure the image is of type uint8
    if gray_image.dtype != 'uint8':
        gray_image = gray_image.astype('uint8')

    contrast_enhanced_image = cv2.equalizeHist(gray_image)  # Equalize on gray image
    return contrast_enhanced_image

# Create a function to load and preprocess images from a folder
def load_and_preprocess_images(folder, label):
    images = []
    labels = []
    for filename in os.listdir(folder):
        if filename.endswith(".jpg"):
            image = cv2.imread(os.path.join(folder, filename))
            if image is not None:
                preprocessed_image = preprocess_image(image)
                images.append(preprocessed_image)
                labels.append(label)
    return images, labels

# Create a function to create and compile the TensorFlow model
def create_and_compile_model():
    model = Sequential()
    model.add(Conv2D(32, kernel_size=(3, 3), activation='relu', input_shape=(100, 100, 3)))
    model.add(MaxPooling2D(pool_size=(2, 2)))
    model.add(Conv2D(64, kernel_size=(3, 3), activation='relu'))
    model.add(MaxPooling2D(pool_size=(2, 2)))
    model.add(Flatten())
    model.add(Dense(128, activation='relu'))
    model.add(Dropout(0.5))
    model.add(Dense(2, activation='softmax'))

    model.compile(loss='categorical_crossentropy', optimizer=Adam(lr=0.001), metrics=['accuracy'])
    return model

def start_training():
    num_epochs = int(epochs_entry.get())  # Get the number of epochs from the Tkinter entry field
    train_model(num_epochs)  # Call the existing train_model function with the number of epochs


# Create a function to train the model
def train_model(epochs):
    global with_flux_folder, without_flux_folder, output_folder
    filter_types = ['blur', 'sharpen', 'edge_detection']

    # Load and preprocess the original images
    with_flux_images, with_flux_labels = load_and_preprocess_images(with_flux_folder, 1)
    without_flux_images, without_flux_labels = load_and_preprocess_images(without_flux_folder, 0)

    # Apply each filter type to the images
    filtered_with_flux_images = []
    filtered_without_flux_images = []
    for filter_type in filter_types:
        filtered_with_flux_images += [apply_filter(image, filter_type) for image in with_flux_images]
        filtered_without_flux_images += [apply_filter(image, filter_type) for image in without_flux_images]

    # Enhance the contrast
    enhanced_with_flux_images = [enhance_contrast(image) for image in filtered_with_flux_images]
    enhanced_without_flux_images = [enhance_contrast(image) for image in filtered_without_flux_images]

    


   
    # Combine and shuffle the data
    all_images = with_flux_images + without_flux_images
    all_labels = with_flux_labels + without_flux_labels
    X_train, X_test, y_train, y_test = train_test_split(all_images, all_labels, test_size=0.2, random_state=42)

    # One-hot encode the labels
    y_train_onehot = np.eye(2)[y_train]
    y_test_onehot = np.eye(2)[y_test]

    # Create and compile the model
    model = create_and_compile_model()
    
    # Data Augmentation
    datagen = ImageDataGenerator(
        rotation_range=20,
        width_shift_range=0.2,
        height_shift_range=0.2,
        horizontal_flip=True)
    datagen.fit(np.array(X_train))

    # Early stopping
    early_stopping = EarlyStopping(monitor='val_loss', patience=3)

    # Train the model
    model.fit(datagen.flow(np.array(X_train), np.array(y_train), batch_size=32),
              epochs=int(epochs_entry.get()), 
              validation_data=(np.array(X_test), np.array(y_test)), 
              callbacks=[early_stopping])

    # Save the model to the output folder
    model.save(os.path.join(output_folder, model_file))
    print("Model Saved")

# Create the main window
window = tk.Tk()
window.title("Flux Stain Detector")
window.geometry("500x400")

# Create labels and buttons for input folders and labels to display folder paths
with_flux_label = tk.Label(window, text="With Flux Folder:")
with_flux_label.pack()
with_flux_display = tk.Label(window, text="Not Selected")
with_flux_display.pack()
with_flux_button = tk.Button(window, text="Browse", command=lambda: browse_input_folders("With Flux", with_flux_display))
with_flux_button.pack()

without_flux_label = tk.Label(window, text="Without Flux Folder:")
without_flux_label.pack()
without_flux_display = tk.Label(window, text="Not Selected")
without_flux_display.pack()
without_flux_button = tk.Button(window, text="Browse", command=lambda: browse_input_folders("Without Flux", without_flux_display))
without_flux_button.pack()

# Create a label and button for the output folder and a label to display folder path
output_label = tk.Label(window, text="Output Folder:")
output_label.pack()
output_display = tk.Label(window, text="Not Selected")
output_display.pack()
output_button = tk.Button(window, text="Browse", command=lambda: browse_output_folder(output_display))
output_button.pack()

#have the user enter the amount of epoch in the window
# Create a label and entry field for the number of epochs
epochs_label = tk.Label(window, text="Number of Epochs:")
epochs_label.pack()
epochs_entry = tk.Entry(window)
epochs_entry.pack()

start_button = tk.Button(window, text="Start Training", command=start_training)
start_button.pack()

window.mainloop()