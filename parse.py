from selenium import webdriver
from PIL import Image
import time
import os
import io


def main():
    driver = webdriver.Chrome()
    driver.get('https://tombatossals.github.io/react-chords/ukulele')
    driver.set_window_size(700, 440)
    time.sleep(2)
    grid = driver.find_element_by_xpath("/html/body/div/div/div/main/div/div")
    chords = grid.find_elements_by_tag_name("a")

    path = None
    cnt = 0
    for chord in chords:
        note = chord.find_element_by_tag_name("p")
        cnt += 1

        bytes = chord.screenshot_as_png
        image = Image.open(io.BytesIO(bytes))
        path = os.path.join(f".\\database\\ukulele\\{note.text[0]}")
        if not os.path.exists(path):
            os.mkdir(path)
            print(f"Made {path}")
        chord_name = str(note.text).replace("/", "slash")
        image.save(f"{path}\\{chord_name}.png")


if __name__ == '__main__':
    # main()
    pass