"""
Логика для взаимодействия с базой данных материалов с коэффициентами звукопоглощения
По данным СП 415.1325800.2018 и других нормативных документов
"""
import json

# Загрузка материалов
def load_materials(file_path="materials.json") -> dict:
    """
    Загружает базу материалов из JSON и преобразует ключи частот в int
    """
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Преобразуем ключи частот из строк в int
    for material, freqs in data.items():
        data[material] = {int(freq): coeff for freq, coeff in freqs.items()}
    
    return data

# Загрузка словаря surface_materials
def load_surface_materials(file_path="surface_materials.json") -> dict:
    """
    Загружает словарь surface_materials из JSON
    """
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data

# Получить список всех материалов
def get_material_names(materials: dict) -> list:
    return list(materials.keys())

# Получить коэффициенты звукопоглощения
def get_material_coefficients(materials: dict, material_name: str) -> dict:
    if material_name not in materials:
        raise ValueError(f"Материал '{material_name}' не найден в базе данных")
    return {int(freq): value for freq, value in materials[material_name].items()}

# Частотные полосы
def get_frequency_bands() -> list:
    return [125, 250, 500, 1000, 2000, 4000]

# Список материалов по типу поверхности
def get_materials_by_surface_type(surface_materials: dict, surface_type: str) -> list:
    return surface_materials.get(surface_type, [])
