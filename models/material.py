"""
Модель материала для акустических расчетов
"""
from typing import Dict

class Material:
    """
    Класс для представления строительного материала с его акустическими характеристиками
    """
    
    def __init__(self, name: str, surface_type: str, area: float, absorption_coefficients: Dict[int, float], category: str = "Ограждающие конструкции"):
        """
        Инициализация материала
        
        Args:
            name: Наименование материала
            surface_type: Тип поверхности (Стены, Потолок, Пол, Остекление, Двери)
            area: Площадь материала в м²
            absorption_coefficients: Коэффициенты звукопоглощения для разных частот
            category: Категория материала (Ограждающие конструкции или Акустические конструкции)
        """
        self.name = name
        self.surface_type = surface_type
        self.area = area
        self.category = category
        self.absorption_coefficients = absorption_coefficients.copy()
        
        # Валидация входных данных
        if not name.strip():
            raise ValueError("Наименование материала не может быть пустым")
        
        if area <= 0:
            raise ValueError("Площадь материала должна быть положительным числом")
        
        if surface_type not in ["Стены", "Потолок", "Пол", "Остекление", "Двери"]:
            raise ValueError("Недопустимый тип поверхности")
        
        if category not in ["Ограждающие конструкции", "Акустические конструкции"]:
            raise ValueError("Недопустимая категория материала")
        
        # Проверяем, что коэффициенты звукопоглощения находятся в допустимых пределах
        for freq, coeff in absorption_coefficients.items():
            if not isinstance(freq, int) or freq <= 0:
                raise ValueError("Частота должна быть положительным целым числом")
            
            if not (0 <= coeff <= 1.0):
                raise ValueError(f"Коэффициент звукопоглощения для частоты {freq} Гц должен быть в диапазоне [0, 1]")
    
    def get_absorption_coefficient(self, frequency: int) -> float:
        """
        Получить коэффициент звукопоглощения для заданной частоты
        
        Args:
            frequency: Частота в Гц
            
        Returns:
            Коэффициент звукопоглощения
        """
        if frequency not in self.absorption_coefficients:
            raise ValueError(f"Коэффициент звукопоглощения для частоты {frequency} Гц не найден")
        
        return self.absorption_coefficients[frequency]
    
    def set_absorption_coefficient(self, frequency: int, coefficient: float) -> None:
        """
        Установить коэффициент звукопоглощения для заданной частоты
        
        Args:
            frequency: Частота в Гц
            coefficient: Коэффициент звукопоглощения
        """
        if not isinstance(frequency, int) or frequency <= 0:
            raise ValueError("Частота должна быть положительным целым числом")
        
        if not (0 <= coefficient <= 1.0):
            raise ValueError("Коэффициент звукопоглощения должен быть в диапазоне [0, 1]")
        
        self.absorption_coefficients[frequency] = coefficient
    
    def calculate_absorption_area(self, frequency: int) -> float:
        """
        Рассчитать площадь звукопоглощения для заданной частоты
        
        Args:
            frequency: Частота в Гц
            
        Returns:
            Площадь звукопоглощения в м²
        """
        coefficient = self.get_absorption_coefficient(frequency)
        return self.area * coefficient
    
    def update_area(self, new_area: float) -> None:
        """
        Обновить площадь материала
        
        Args:
            new_area: Новая площадь в м²
        """
        if new_area <= 0:
            raise ValueError("Площадь материала должна быть положительным числом")
        
        self.area = new_area
    
    def get_available_frequencies(self) -> list:
        """
        Получить список доступных частот
        
        Returns:
            Список частот в Гц
        """
        return sorted(self.absorption_coefficients.keys())
    
    def __str__(self) -> str:
        """Строковое представление материала"""
        return f"{self.name} ({self.surface_type}): {self.area:.2f} м²"
    
    def __repr__(self) -> str:
        """Представление для отладки"""
        return f"Material(name='{self.name}', surface_type='{self.surface_type}', area={self.area})"
