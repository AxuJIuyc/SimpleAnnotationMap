import cv2
import os
from tqdm import tqdm

# Путь к директории с изображениями
folder_path = 'data/Germany'

# Пороговое значение для определения черного цвета
black_threshold = 30  # Процент площади черного цвета

# Функция для определения процента черного цвета на изображении
def calculate_black_percentage(image_path):
    image = cv2.imread(image_path)
    if image is None:
        return 0  # Изображение не удалось загрузить

    # Преобразование в оттенки серого
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Вычисление порогового значения для черного цвета
    _, black_and_white_image = cv2.threshold(gray_image, 0, 255, cv2.THRESH_BINARY)
    
    # Вычисление процента черного цвета
    total_pixels = black_and_white_image.size
    white_pixels = cv2.countNonZero(black_and_white_image)
    percentage_black = 100 - (white_pixels / total_pixels) * 100

    return percentage_black

def run(folder_path, black_threshold):
    masks_path = f'{folder_path}/masks'
    sources_path = f'{folder_path}/sources'
    html_path = f'{folder_path}/html'
    download_path = f'{folder_path}/download'
    geojson_path = f'{folder_path}/geojson'
    json_path = f'{folder_path}/jsons'

    # Пройти по всем файлам в директории и удалить те, на которых черного цвета больше 20%
    deleted_list = []
    files = os.listdir(masks_path)
    for filename, _ in zip(files, tqdm(range(len(files)))):
        name = os.path.splitext(filename)[0]
        image_path = os.path.join(masks_path, filename)
        
        # Проверить, является ли файл изображением
        if os.path.isfile(image_path) and image_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
            black_percentage = calculate_black_percentage(image_path)
            
            if black_percentage > black_threshold:
                os.remove(image_path)
                deleted_list.append(filename)

                source_file = f'{sources_path}/{filename}'
                if os.path.exists(source_file):
                    os.remove(source_file)
                json_file = f'{json_path}/{name}.json'
                if os.path.exists(json_file):
                    os.remove(json_file)
                geojson_file = f'{geojson_path}/{name}.geojson'
                if os.path.exists(geojson_file):
                    os.remove(geojson_file)
                html_file = f'{html_path}/{name}_op0.2.html'
                if os.path.exists(html_file):
                    os.remove(html_file)
                download_file = f'{sources_path}/{filename}'
                if os.path.exists(download_file):
                    os.remove(download_file)

    print(f'Было удалено {len(deleted_list)} изображений:')
    print(deleted_list)

if __name__ == '__main__':
    run(folder_path, black_threshold)