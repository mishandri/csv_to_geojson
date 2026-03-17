import csv
import json
import sys
import os

csv.field_size_limit(1024 * 1024 * 1024)

def swap_coords(coord_list):
    """
    Меняет местами координаты из формата [lat, lon] в [lon, lat]
    """
    if not isinstance(coord_list, list):
        return coord_list
    
    if not coord_list:
        return coord_list
    
    # Если первый элемент - число, значит это координата
    if isinstance(coord_list[0], (int, float)):
        if len(coord_list) >= 2:
            return [coord_list[1], coord_list[0]]
        return coord_list
    
    # Если первый элемент - список, рекурсивно обрабатываем
    return [swap_coords(item) for item in coord_list]

def csv_to_geojson(csv_file_path, output_file_path=None):
    """
    Конвертирует CSV-файл с геоданными регионов в формат GeoJSON.
    """
    if output_file_path is None:
        output_file_path = os.path.splitext(csv_file_path)[0] + '.geojson'
    
    # Создаём структуру GeoJSON (как в рабочем файле)
    geojson = {
        "type": "FeatureCollection",
        "features": []
    }
    
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=';')
            
            success_count = 0
            error_count = 0
            
            for row_num, row in enumerate(reader, start=2):
                try:
                    name = row.get('name', '').strip()
                    coords_str = row.get('coords', '').strip()
                    
                    if not name or not coords_str:
                        print(f"Предупреждение: Строка {row_num} пропущена")
                        continue
                    
                    # Парсим координаты
                    coords_str = coords_str.strip('"').replace("'", '"')
                    coordinates = json.loads(coords_str)
                    
                    # Определяем тип геометрии
                    # В CSV все регионы - MultiPolygon (двойные скобки)
                    geometry_type = "MultiPolygon"
                    
                    # Меняем координаты местами [lat, lon] -> [lon, lat]
                    coordinates = swap_coords(coordinates)
                    
                    # Создаём feature (как в рабочем файле)
                    feature = {
                        "type": "Feature",
                        "properties": {
                            "name": name,
                            "type": row.get('type', '').strip(),
                            "id": row.get('id', '').strip(),
                            "region": row.get('region', '').strip(),
                            "coords_type": row.get('coords_type', '').strip()
                        },
                        "geometry": {
                            "type": geometry_type,
                            "coordinates": coordinates
                        }
                    }
                    
                    geojson["features"].append(feature)
                    success_count += 1
                    print(f"✓ Обработан: {name}")
                    
                except json.JSONDecodeError as e:
                    print(f"✗ Ошибка парсинга JSON в строке {row_num}: {e}")
                    error_count += 1
                except Exception as e:
                    print(f"✗ Неожиданная ошибка в строке {row_num}: {e}")
                    error_count += 1
            
            # Сохраняем результат
            with open(output_file_path, 'w', encoding='utf-8') as outfile:
                json.dump(geojson, outfile, ensure_ascii=False, indent=2)
            
            print(f"\nКонвертация завершена!")
            print(f"   Входной файл: {csv_file_path}")
            print(f"   Выходной файл: {output_file_path}")
            print(f"   Успешно: {success_count}, Ошибок: {error_count}")
            
            return geojson
            
    except FileNotFoundError:
        print(f"Ошибка: Файл '{csv_file_path}' не найден")
        return None
    except Exception as e:
        print(f"Ошибка при чтении CSV: {e}")
        return None

def main():
    if len(sys.argv) < 2:
        print("Использование:")
        print("  python csv_to_geojson.py <путь_к_csv_файлу> [путь_для_выходного_файла]")
        print("\nПример:")
        print("  python csv_to_geojson.py ru_regions.csv")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    csv_to_geojson(input_file, output_file)

if __name__ == "__main__":
    main()