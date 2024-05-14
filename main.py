import os
from random import randint
import sys
import shutil

from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QMessageBox,
    QLabel,
    QFileDialog,
    QMainWindow,
    QRadioButton,
    QVBoxLayout,
    QPushButton,
    QButtonGroup,
)

from PIL import Image


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image Optimizer")
        layout = QVBoxLayout()

        """ Select profile part """
        label1 = QLabel("1. Sélectionnez un profil:")
        self.profile_group = QButtonGroup(self)  # Create a button group

        self.selected_profile = ""
        self.lith_profile = QRadioButton("Lith")
        self.tys_profile = QRadioButton("Tys")
        self.profile_group.addButton(self.lith_profile)
        self.profile_group.addButton(self.tys_profile)

        self.lith_profile.clicked.connect(self.set_profile)
        self.tys_profile.clicked.connect(self.set_profile)

        """ Select operation part """
        label3 = QLabel("3. Sélectionnez l'opération:")
        self.operation_group = QButtonGroup(self)  # Create a button group

        self.selected_operation = ""
        self.resize_crop_operation = QRadioButton("Resize and Crop")
        self.thumbnail_operation = QRadioButton("Create Thumbnail")
        self.operation_group.addButton(self.resize_crop_operation)
        self.operation_group.addButton(self.thumbnail_operation)

        self.resize_crop_operation.clicked.connect(self.set_operation)
        self.thumbnail_operation.clicked.connect(self.set_operation)

        """ Select files part """
        label2 = QLabel("2. Sélectionnez la/les images:")
        select_files_button = QPushButton("Sélectionner les fichiers")
        select_files_button.clicked.connect(self.open_dialog)

        self.callback = QLabel("")

        """ Mount layout part """
        layout.addWidget(label1)
        layout.addWidget(self.lith_profile)
        layout.addWidget(self.tys_profile)
        layout.addWidget(label2)
        layout.addWidget(select_files_button)
        layout.addWidget(label3)
        layout.addWidget(self.resize_crop_operation)
        layout.addWidget(self.thumbnail_operation)
        layout.addWidget(self.callback)

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

    def set_profile(self):
        """Set self.selected_profile depending on the radio button checked"""
        if self.lith_profile.isChecked():
            self.selected_profile = "lith"
            print("Profile set to: lith")
        elif self.tys_profile.isChecked():
            self.selected_profile = "tys"
            print("Profile set to: tys")

    def set_operation(self):
        """Set self.selected_operation depending on the radio button checked"""
        if self.resize_crop_operation.isChecked():
            self.selected_operation = "resize_crop"
            print("Operation set to: resize_crop")
        elif self.thumbnail_operation.isChecked():
            self.selected_operation = "thumbnail"
            print("Operation set to: thumbnail")

    def open_dialog(self):
        """Ensure a profile and operation are selected,
        if not, display a warning modal,
        else launch file explorer modal
        """

        if not self.selected_profile:
            dialog = QMessageBox(self)
            dialog.setWindowTitle("Erreur")
            dialog.setText("Choisissez d'abord un profil")
            dialog.exec()

        elif not self.selected_operation:
            dialog = QMessageBox(self)
            dialog.setWindowTitle("Erreur")
            dialog.setText("Choisissez d'abord une opération")
            dialog.exec()

        else:
            file_filter = "Images (*.png *.jpg *.jpeg *.webp)"
            response = QFileDialog.getOpenFileNames(
                caption="Sélectionnez une ou plusieurs images",
                directory=os.getcwd(),
                filter=file_filter,
            )
            if response[0]:
                # Check if images meet the required size
                if not check_image_sizes(self, response[0], self.selected_profile):
                    return

                status, message = optimize(
                    self, response[0], self.selected_profile, self.selected_operation
                )
                if status == 0:
                    self.callback.setText(
                        f"Les images ont été sauvegardées dans le dossier {message}"
                    )
                    os.startfile(message)  # Open directory with file explorer
                else:
                    self.callback.setText(
                        "Erreur lors de l'optimisation des images: " + message
                    )


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()


def check_image_sizes(parent, file_paths: list[str], profile: str) -> bool:
    """Check if all images meet the required size for the selected profile"""
    image_sizes = {
        "3:4": (900, 1200),
        "4:4": (900, 900),
    }

    max_width, max_height = image_sizes[profile]

    for file_path in file_paths:
        with Image.open(file_path) as im:
            img_width, img_height = im.size
            if img_width < max_width or img_height < max_height:
                QMessageBox.critical(
                    parent,
                    "Erreur",
                    f"L'image {file_path} a une taille de {img_width}x{img_height} pixels, "
                    f"qui est plus petite que la taille requise de {max_width}x{max_height} pixels.",
                )
                return False

    return True


def optimize(parent, files_paths: list[str], profile: str, operation: str) -> tuple:
    """Optimize images for web,
    for each file in the files_path list:
    crop and resize the image in 2 sizes depending on profile selected
    or create a thumbnail
    give random number name to image for CDN optimization
    and create a new directory named product_images in the same folder as the images
    """
    profiles = ["lith", "tys"]
    image_sizes = {
        "lith": {"sm": (300, 400), "md": (600, 800), "lg": (900, 1200)},
        "tys": {"sm": (300, 300), "md": (600, 600), "lg": (900, 900)},
    }

    if profile not in profiles:
        return 1, "Profile not found"

    output_dir = os.path.join(os.path.dirname(files_paths[0]), "product_images")
    if os.path.exists(output_dir):
        reply = QMessageBox.question(
            parent,
            "Confirmation",
            f"The folder '{output_dir}' already exists. Do you want to override it?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.No:
            return 1, "User chose not to override the existing folder"
        else:
            shutil.rmtree(output_dir)  # Delete the existing directory and its contents
            os.makedirs(output_dir)
    else:
        os.makedirs(output_dir)

    for file_path in files_paths:
        random_number = str(
            randint(10000000, 99999999)
        )  # Generate a random 8-digit number

        with Image.open(file_path) as im:
            for size_key, dimensions in image_sizes[profile].items():
                if operation == "resize_crop":
                    optimized_image = resize_and_crop(im, dimensions)
                elif operation == "thumbnail":
                    optimized_image = create_thumbnail(im, dimensions)
                else:
                    return 1, "Operation not supported"

                new_filename = f"{size_key}_{random_number}.webp"
                output_path = os.path.join(output_dir, new_filename)
                optimized_image.save(output_path, "webp", optimize=True, quality=85)
                print(f"Saved {output_path}")

    return 0, output_dir


def resize_and_crop(image: Image, dimensions: tuple[int, int]) -> Image:
    """Resize and crop the image to the specified dimensions."""
    # Calculate the scaling factor needed to resize the image to cover the target size.
    img_width, img_height = image.size
    width_ratio = dimensions[0] / img_width
    height_ratio = dimensions[1] / img_height
    if width_ratio > height_ratio:
        new_width = dimensions[0]
        new_height = int(img_height * width_ratio)
    else:
        new_width = int(img_width * height_ratio)
        new_height = dimensions[1]

    # Resize the image with the calculated dimensions.
    resized_image = image.resize((new_width, new_height))

    # Calculate top-left corner of the crop box.
    left = (new_width - dimensions[0]) // 2
    top = (new_height - dimensions[1]) // 2

    # Crop the centered part of the resized image.
    cropped_image = resized_image.crop(
        (left, top, left + dimensions[0], top + dimensions[1])
    )
    return cropped_image


def create_thumbnail(image: Image, dimensions: tuple[int, int]) -> Image:
    """Create a thumbnail of the image maintaining the aspect ratio
    and then crop it to the exact target dimensions."""
    img_width, img_height = image.size
    target_width, target_height = dimensions

    # Calculate the scaling factor needed to resize the image to cover the target size.
    width_ratio = target_width / img_width
    height_ratio = target_height / img_height
    if width_ratio > height_ratio:
        new_width = target_width
        new_height = int(img_height * width_ratio)
    else:
        new_width = int(img_width * height_ratio)
        new_height = target_height

    # Resize the image with the calculated dimensions.
    resized_image = image.resize((new_width, new_height))

    # Calculate top-left corner of the crop box.
    left = (new_width - target_width) // 2
    top = (new_height - target_height) // 2

    # Crop the centered part of the resized image.
    cropped_image = resized_image.crop(
        (left, top, left + target_width, top + target_height)
    )
    return cropped_image


if __name__ == "__main__":
    main()
