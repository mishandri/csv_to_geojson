import csv
import json
import sys
import os

csv.field_size_limit(1024 * 1024 * 1024)  # Увеличиваем лимит до 1 ГБ

def csv_to_geojson(csv_file_path, output_file_path=None):
    """
    Конвертирует CSV-файл с геоданными регионов в формат GeoJSON.
    
    Аргументы:
        csv_file_path (str): Путь к входному CSV-файлу
        output_file_path (str, optional): Путь для сохранения GeoJSON. 
                                          Если не указан, сохраняет в ту же папку с расширением .geojson
    
    Возвращает:
        dict: GeoJSON объект в виде словаря Python
    """
    
    # Если путь для вывода не указан, создаём его на основе входного файла
    if output_file_path is None:
        output_file_path = os.path.splitext(csv_file_path)[0] + '.geojson'
    
    # Создаём структуру GeoJSON
    geojson = {
        "type": "FeatureCollection",
        "name": "ru_regions",
        "crs": [{
            "type": "name",
            "properties": {
                "name": "urn:ogc:def:crs:OGC:1.3:CRS84"
            }
        }],
        "features": []
    }
    
    try:
        # Открываем и читаем CSV-файл
        with open(csv_file_path, 'r', encoding='utf-8') as csvfile:
            # Читаем CSV с разделителем точка с запятой
            reader = csv.DictReader(csvfile, delimiter=';')
            
            for row_num, row in enumerate(reader, start=2):  # start=2 для учёта заголовка
                try:
                    # Извлекаем данные из строки
                    name = row.get('name', '').strip()
                    region_type = row.get('type', '').strip()
                    region_id = row.get('id', '').strip()
                    region_full = row.get('region', '').strip()
                    coords_type = row.get('coords_type', '').strip()
                    coords_str = row.get('coords', '').strip()
                    
                    # Пропускаем пустые строки
                    if not name or not coords_str:
                        print(f"Предупреждение: Строка {row_num} пропущена - отсутствуют имя или координаты")
                        continue
                    
                    # Парсим координаты
                    # Убираем внешние кавычки и обрабатываем строку
                    coords_str = coords_str.strip('"')
                    
                    # Заменяем одиночные кавычки на двойные для JSON-совместимости
                    coords_str = coords_str.replace("'", '"')
                    
                    # Парсим JSON
                    coordinates = json.loads(coords_str)
                    
                    # Проверяем, что координаты - это список
                    if not isinstance(coordinates, list):
                        print(f"Ошибка в строке {row_num}: координаты не являются списком")
                        continue
                    
                    # GeoJSON ожидает координаты в формате [longitude, latitude]
                    # Конвертируем из [latitude, longitude] в [longitude, latitude]
                    def swap_coords(coord_list):
                        """Рекурсивно меняет местами координаты во вложенных списках"""
                        if isinstance(coord_list[0], list):
                            return [swap_coords(item) for item in coord_list]
                        else:
                            # Предполагаем, что формат [lat, lon] -> меняем на [lon, lat]
                            if len(coord_list) >= 2:
                                return [coord_list[1], coord_list[0]]
                            return coord_list
                    
                    # Меняем координаты местами
                    coordinates = swap_coords(coordinates)
                    
                    # Создаём feature
                    feature = {
                        "type": "Feature",
                        "properties": {
                            "name": name,
                            "type": region_type,
                            "id": region_id,
                            "region": region_full,
                            "coords_type": coords_type
                        },
                        "geometry": {
                            "type": "MultiPolygon",
                            "coordinates": coordinates
                        }
                    }
                    
                    geojson["features"].append(feature)
                    print(f"Обработан регион: {name}")
                    
                except json.JSONDecodeError as e:
                    print(f"Ошибка парсинга JSON в строке {row_num}: {e}")
                    print(f"Проблемная строка: {coords_str[:100]}...")
                    continue
                except Exception as e:
                    print(f"Неожиданная ошибка в строке {row_num}: {e}")
                    continue
        
        # Сохраняем результат
        with open(output_file_path, 'w', encoding='utf-8') as outfile:
            json.dump(geojson, outfile, ensure_ascii=False, indent=2)
        
        print(f"\nУспешно сконвертировано!")
        print(f"   Входной файл: {csv_file_path}")
        print(f"   Выходной файл: {output_file_path}")
        print(f"   Обработано регионов: {len(geojson['features'])}")
        
        return geojson
        
    except FileNotFoundError:
        print(f"Ошибка: Файл '{csv_file_path}' не найден")
        return None
    except Exception as e:
        print(f"Ошибка при чтении CSV: {e}")
        return None


def main():
    """Основная функция для запуска скрипта из командной строки"""
    
    # Проверяем аргументы командной строки
    if len(sys.argv) < 2:
        print("Использование:")
        print("  python csv_to_geojson.py <путь_к_csv_файлу> [путь_для_выходного_файла]")
        print("\nПример:")
        print("  python csv_to_geojson.py ru_regions.csv")
        print("  python csv_to_geojson.py ru_regions.csv my_map.geojson")
        sys.exit(1)
    
    # Получаем путь к входному файлу
    input_file = sys.argv[1]
    
    # Получаем путь к выходному файлу (если указан)
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Запускаем конвертацию
    csv_to_geojson(input_file, output_file)


if __name__ == "__main__":
    main()