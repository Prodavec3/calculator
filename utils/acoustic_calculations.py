"""
Утилиты для акустических расчетов времени реверберации
По методике СП 415.1325800.2018
"""
import math
from typing import Dict, Any, Optional
from models.room import Room

def calculate_phi_function(alpha_avg: float) -> float:
    """
    Рассчитать функцию φ(αср) = -ln(1 - αср)

    Args:
        alpha_avg: Средний коэффициент звукопоглощения

    Returns:
        Значение функции φ(αср)
    """
    # Ограничиваем αср чтобы избежать ln(0)
    alpha_avg = min(alpha_avg, 0.99)
    return -math.log(1 - alpha_avg)

def get_air_absorption_coefficient(frequency: int) -> float:
    """
    Получить коэффициент поглощения звука в воздухе n
    По приложению Г СП 415.1325800.2018

    Args:
        frequency: Частота в Гц

    Returns:
        Коэффициент поглощения звука в воздухе
    """
    # Коэффициенты для стандартных условий (20°C, 50% влажности)
    air_absorption_coefficients = {
        125: 0.0000,
        250: 0.0000,
        500: 0.0000,
        1000: 0.0000,
        2000: 0.0010,
        4000: 0.0002
    }

    return air_absorption_coefficients.get(frequency, 0.0006)


def calculate_reverberation_time_for_frequency(
    room: Room,
    frequency: int,
    alpha_avg: float,
    equivalent_absorption_area: float,
    surface_area: Optional[float] = None,
    has_acoustic_materials: bool = False
) -> float:
    """
    Рассчитать время реверберации для конкретной частоты (корректная методика СП 415)
    с учетом эффективной площади и формулы φ(αср).
    """
    # Определяем эффективную площадь
    if surface_area is None:
        surface_area = room.total_surface_area

    if has_acoustic_materials:
        # Вычитаем площадь акустических материалов из общей площади
        acoustic_area_total = sum(mat.area for mat in room.materials if mat.category == "Акустические конструкции")
        effective_surface_area = surface_area - acoustic_area_total
    else:
        effective_surface_area = surface_area

    # Средний коэффициент звукопоглощения
    avg_alpha = equivalent_absorption_area / effective_surface_area

    # Функция φ(αср)
    phi_value = calculate_phi_function(avg_alpha)

    # Вычисляем время реверберации
    if frequency <= 1000:
        denominator = effective_surface_area * phi_value
    else:
        n = get_air_absorption_coefficient(frequency)
        denominator = effective_surface_area * phi_value + n * room.volume

    if denominator == 0:
        raise ValueError("Знаменатель в формуле расчета времени реверберации равен нулю")

    return (0.163 * room.volume) / denominator


def calculate_structural_reverberation_time(room: Room) -> Dict[str, Any]:
    """
    Выполнить расчет времени реверберации только с ограждающими конструкциями

    Args:
        room: Объект помещения с материалами

    Returns:
        Словарь с результатами расчетов
    """
    if not room.materials:
        raise ValueError("В помещении не указаны материалы")

    # Частоты для расчета
    frequencies = [125, 250, 500, 1000, 2000, 4000]

    # Рассчитать критическую частоту
    critical_frequency = room.calculate_critical_frequency()

    # Инициализация результатов
    results = {
        'calculation_type': 'Ограждающие конструкции',
        'critical_frequency': critical_frequency,
        'reverberation_times': {},
        'average_absorption_coefficients': {},
        'equivalent_absorption_areas': {},
        'phi_values': {},
        'room_volume': room.volume,
        'total_surface_area': room.total_surface_area,
        'effective_surface_area': room.get_effective_surface_area()
    }

    # Расчет для каждой частоты
    for frequency in frequencies:
        try:
            # Рассчитать эквивалентную площадь звукопоглощения
            equivalent_absorption_area = room.calculate_structural_absorption_area(frequency)

            # Рассчитать средний коэффициент звукопоглощения
            alpha_avg = room.calculate_structural_average_absorption_coefficient(frequency)

            # Рассчитать функцию φ(αср)
            phi_value = calculate_phi_function(alpha_avg)

            # Рассчитать время реверберации с использованием эффективной площади
            effective_surface_area = room.get_effective_surface_area()
            reverberation_time = calculate_reverberation_time_for_frequency(
                room, frequency, alpha_avg, equivalent_absorption_area, effective_surface_area
            )

            # Сохранить результаты
            results['reverberation_times'][frequency] = reverberation_time
            results['average_absorption_coefficients'][frequency] = alpha_avg
            results['equivalent_absorption_areas'][frequency] = equivalent_absorption_area
            results['phi_values'][frequency] = phi_value

        except Exception as e:
            raise ValueError(f"Ошибка при расчете для частоты {frequency} Гц: {str(e)}")

    # Валидация результатов
    validate_calculation_results(results)

    return results

def calculate_combined_reverberation_time(room: Room) -> Dict[str, Any]:
    """
    Выполнить расчет времени реверберации с учетом акустических материалов

    Args:
        room: Объект помещения с материалами

    Returns:
        Словарь с результатами расчетов
    """
    if not room.materials:
        raise ValueError("В помещении не указаны материалы")

    # Частоты для расчета
    frequencies = [125, 250, 500, 1000, 2000, 4000]

    # Рассчитать критическую частоту
    critical_frequency = room.calculate_critical_frequency()

    # Инициализация результатов
    results = {
        'calculation_type': 'С учетом акустических материалов',
        'critical_frequency': critical_frequency,
        'reverberation_times': {},
        'average_absorption_coefficients': {},
        'equivalent_absorption_areas': {},
        'structural_absorption_areas': {},
        'acoustic_absorption_areas': {},
        'phi_values': {},
        'room_volume': room.volume,
        'total_surface_area': room.total_surface_area,
        'effective_surface_area': room.get_effective_surface_area()
    }

    # Расчет для каждой частоты
    for frequency in frequencies:
        try:
            # Рассчитать эквивалентную площадь звукопоглощения
            equivalent_absorption_area = room.calculate_equivalent_absorption_area(frequency)
            structural_absorption_area = room.calculate_structural_absorption_area(frequency)
            acoustic_absorption_area = room.calculate_acoustic_absorption_area(frequency)

            # Рассчитать средний коэффициент звукопоглощения
            alpha_avg = room.calculate_combined_average_absorption_coefficient(frequency)

            # Рассчитать функцию φ(αср)
            phi_value = calculate_phi_function(alpha_avg)

            # Рассчитать время реверберации
            reverberation_time = calculate_reverberation_time_for_frequency(
                room, frequency, alpha_avg, equivalent_absorption_area
            )

            # Сохранить результаты
            results['reverberation_times'][frequency] = reverberation_time
            results['average_absorption_coefficients'][frequency] = alpha_avg
            results['equivalent_absorption_areas'][frequency] = equivalent_absorption_area
            results['structural_absorption_areas'][frequency] = structural_absorption_area
            results['acoustic_absorption_areas'][frequency] = acoustic_absorption_area
            results['phi_values'][frequency] = phi_value

        except Exception as e:
            raise ValueError(f"Ошибка при расчете для частоты {frequency} Гц: {str(e)}")

    # Валидация результатов
    validate_calculation_results(results)

    return results

def calculate_reverberation_time(room: Room) -> Dict[str, Any]:
    """
    Выполнить полный расчет времени реверберации для помещения (старая версия, для обратной совместимости)

    Args:
        room: Объект помещения с материалами

    Returns:
        Словарь с результатами расчетов
    """
    if not room.materials:
        raise ValueError("В помещении не указаны материалы")

    # Частоты для расчета
    frequencies = [125, 250, 500, 1000, 2000, 4000]

    # Рассчитать критическую частоту
    critical_frequency = room.calculate_critical_frequency()

    # Инициализация результатов
    results = {
        'critical_frequency': critical_frequency,
        'reverberation_times': {},
        'average_absorption_coefficients': {},
        'equivalent_absorption_areas': {},
        'phi_values': {},
        'room_volume': room.volume,
        'total_surface_area': room.total_surface_area
    }

    # Расчет для каждой частоты
    for frequency in frequencies:
        try:
            # Рассчитать эквивалентную площадь звукопоглощения
            equivalent_absorption_area = room.calculate_equivalent_absorption_area(frequency)

            # Рассчитать средний коэффициент звукопоглощения
            alpha_avg = room.calculate_average_absorption_coefficient(frequency)

            # Рассчитать функцию φ(αср)
            phi_value = calculate_phi_function(alpha_avg)

            # Рассчитать время реверберации
            reverberation_time = calculate_reverberation_time_for_frequency(
                room, frequency, alpha_avg, equivalent_absorption_area
            )

            # Сохранить результаты
            results['reverberation_times'][frequency] = reverberation_time
            results['average_absorption_coefficients'][frequency] = alpha_avg
            results['equivalent_absorption_areas'][frequency] = equivalent_absorption_area
            results['phi_values'][frequency] = phi_value

        except Exception as e:
            raise ValueError(f"Ошибка при расчете для частоты {frequency} Гц: {str(e)}")

    # Валидация результатов
    validate_calculation_results(results)

    return results

def validate_calculation_results(results: Dict[str, Any]) -> None:
    """
    Проверить корректность результатов расчета

    Args:
        results: Словарь с результатами расчетов
    """
    frequencies = [125, 250, 500, 1000, 2000, 4000]

    for frequency in frequencies:
        reverberation_time = results['reverberation_times'][frequency]
        alpha_avg = results['average_absorption_coefficients'][frequency]

        # Проверка времени реверберации
        if reverberation_time <= 0:
            raise ValueError(f"Время реверберации для частоты {frequency} Гц должно быть положительным")

        if reverberation_time > 10:
            print(f"Предупреждение: Время реверберации для частоты {frequency} Гц превышает 10 секунд ({reverberation_time:.3f} с)")

        # Проверка среднего коэффициента звукопоглощения
        if not (0 <= alpha_avg <= 1):
            raise ValueError(f"Средний КЗП для частоты {frequency} Гц должен быть в диапазоне [0, 1]")

def get_recommended_reverberation_times(room_purpose: str) -> Dict[int, tuple]:
    """
    Получить рекомендуемые времена реверберации для различных типов помещений

    Args:
        room_purpose: Назначение помещения

    Returns:
        Словарь с рекомендуемыми диапазонами времени реверберации по частотам
    """
    recommendations = {
        "Конференц-зал": {
            125: (0.8, 1.2),
            250: (0.8, 1.2),
            500: (0.8, 1.2),
            1000: (0.8, 1.2),
            2000: (0.8, 1.2),
            4000: (0.8, 1.2)
        },
        "Аудитория": {
            125: (0.8, 1.3),
            250: (0.8, 1.3),
            500: (0.8, 1.3),
            1000: (0.8, 1.3),
            2000: (0.8, 1.3),
            4000: (0.8, 1.3)
        },
        "Концертный зал": {
            125: (1.5, 2.0),
            250: (1.5, 2.0),
            500: (1.5, 2.0),
            1000: (1.5, 2.0),
            2000: (1.4, 1.9),
            4000: (1.3, 1.8)
        },
        "Театральный зал": {
            125: (1.2, 1.6),
            250: (1.2, 1.6),
            500: (1.2, 1.6),
            1000: (1.2, 1.6),
            2000: (1.1, 1.5),
            4000: (1.0, 1.4)
        },
        "Кинотеатр": {
            125: (0.8, 1.2),
            250: (0.8, 1.2),
            500: (0.8, 1.2),
            1000: (0.8, 1.2),
            2000: (0.8, 1.2),
            4000: (0.8, 1.2)
        },
        "Спортивный зал": {
            125: (1.5, 2.5),
            250: (1.5, 2.5),
            500: (1.5, 2.5),
            1000: (1.5, 2.5),
            2000: (1.4, 2.3),
            4000: (1.3, 2.0)
        },
        "Офисное помещение": {
            125: (0.4, 0.8),
            250: (0.4, 0.8),
            500: (0.4, 0.8),
            1000: (0.4, 0.8),
            2000: (0.4, 0.8),
            4000: (0.4, 0.8)
        },
        "Ресторан": {
            125: (0.8, 1.2),
            250: (0.8, 1.2),
            500: (0.8, 1.2),
            1000: (0.8, 1.2),
            2000: (0.8, 1.2),
            4000: (0.8, 1.2)
        }
    }

    return recommendations.get(room_purpose, {})

def compare_with_recommendations(results: Dict[str, Any], room_purpose: str) -> Dict[str, str]:
    """
    Сравнить результаты расчета с рекомендуемыми значениями

    Args:
        results: Результаты расчета времени реверберации
        room_purpose: Назначение помещения

    Returns:
        Словарь с оценками для каждой частоты
    """
    recommendations = get_recommended_reverberation_times(room_purpose)
    comparisons = {}

    if not recommendations:
        return comparisons

    for frequency in [125, 250, 500, 1000, 2000, 4000]:
        if frequency in results['reverberation_times'] and frequency in recommendations:
            calculated_time = results['reverberation_times'][frequency]
            min_recommended, max_recommended = recommendations[frequency]

            if calculated_time < min_recommended:
                comparisons[frequency] = f"Низкое ({calculated_time:.3f} с < {min_recommended} с)"
            elif calculated_time > max_recommended:
                comparisons[frequency] = f"Высокое ({calculated_time:.3f} с > {max_recommended} с)"
            else:
                comparisons[frequency] = f"Норма ({min_recommended}-{max_recommended} с)"

    return comparisons
