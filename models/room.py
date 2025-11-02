"""
Модель помещения для акустических расчетов
"""
import math
from typing import List, Dict, Optional
from .material import Material

class Room:
    """
    Класс для представления помещения с его геометрическими характеристиками
    и материалами поверхностей
    """
    
    def __init__(self, name: str, purpose: str, length: Optional[float] = None, width: Optional[float] = None, height: Optional[float] = None,
                 manual_wall_area: Optional[float] = None, manual_floor_area: Optional[float] = None, manual_ceiling_area: Optional[float] = None,
                 manual_volume: Optional[float] = None):
        """
        Инициализация помещения
        
        Args:
            name: Наименование помещения
            purpose: Назначение помещения
            length: Длина помещения (м) - для прямоугольных помещений
            width: Ширина помещения (м) - для прямоугольных помещений
            height: Высота помещения (м) - для прямоугольных помещений
            manual_wall_area: Площадь стен (м²) - для ручного ввода
            manual_floor_area: Площадь пола (м²) - для ручного ввода
            manual_ceiling_area: Площадь потолка (м²) - для ручного ввода
        """
        self.name = name
        self.purpose = purpose
        self.length = length
        self.width = width
        self.height = height
        self.manual_wall_area = manual_wall_area
        self.manual_floor_area = manual_floor_area
        self.manual_ceiling_area = manual_ceiling_area
        self.manual_volume = manual_volume
        self.materials: List[Material] = []
        
        # Валидация входных данных
        if not name.strip():
            raise ValueError("Наименование помещения не может быть пустым")
            
        # Проверяем, что задан хотя бы один способ определения размеров
        has_dimensions = all([length is not None and length > 0, 
                             width is not None and width > 0, 
                             height is not None and height > 0])
        has_manual_areas = any([manual_wall_area is not None and manual_wall_area > 0,
                               manual_floor_area is not None and manual_floor_area > 0,
                               manual_ceiling_area is not None and manual_ceiling_area > 0])
        
        if not has_dimensions and not has_manual_areas:
            raise ValueError("Необходимо указать либо размеры помещения, либо площади поверхностей вручную")
            
        # Если заданы размеры, проверяем их корректность
        if has_dimensions and (length is not None and width is not None and height is not None):
            if length <= 0 or width <= 0 or height <= 0:
                raise ValueError("Размеры помещения должны быть положительными числами")
            
        # Если заданы площади вручную, проверяем их корректность
        if manual_wall_area is not None and manual_wall_area <= 0:
            raise ValueError("Площадь стен должна быть положительным числом")
        if manual_floor_area is not None and manual_floor_area <= 0:
            raise ValueError("Площадь пола должна быть положительным числом")
        if manual_ceiling_area is not None and manual_ceiling_area <= 0:
            raise ValueError("Площадь потолка должна быть положительным числом")
    
    @property
    def volume(self) -> float:
        """Объем помещения в м³"""
        if self.manual_volume is not None:
            return self.manual_volume
        elif self.length is not None and self.width is not None and self.height is not None:
            return self.length * self.width * self.height
        else:
            raise ValueError("Для расчета объема необходимо указать размеры помещения или объем вручную")
    
    @property
    def total_surface_area(self) -> float:
        """Общая площадь поверхностей помещения в м²"""
        return self.wall_area + self.floor_area + self.ceiling_area
    
    @property
    def wall_area(self) -> float:
        """Площадь стен в м²"""
        if self.manual_wall_area is not None:
            return self.manual_wall_area
        elif self.length is not None and self.width is not None and self.height is not None:
            return 2 * (self.length * self.height + self.width * self.height)
        else:
            raise ValueError("Для расчета площади стен необходимо указать размеры помещения или площадь стен вручную")
    
    @property
    def floor_area(self) -> float:
        """Площадь пола в м²"""
        if self.manual_floor_area is not None:
            return self.manual_floor_area
        elif self.length is not None and self.width is not None:
            return self.length * self.width
        else:
            raise ValueError("Для расчета площади пола необходимо указать размеры помещения или площадь пола вручную")
    
    @property
    def ceiling_area(self) -> float:
        """Площадь потолка в м²"""
        if self.manual_ceiling_area is not None:
            return self.manual_ceiling_area
        elif self.length is not None and self.width is not None:
            return self.length * self.width
        else:
            raise ValueError("Для расчета площади потолка необходимо указать размеры помещения или площадь потолка вручную")
    
    def add_material(self, material: Material) -> None:
        """
        Добавить материал в помещение
        
        Args:
            material: Объект материала
        """
        if not isinstance(material, Material):
            raise ValueError("Материал должен быть экземпляром класса Material")
        
        self.materials.append(material)
    
    def remove_material(self, index: int) -> None:
        """
        Удалить материал по индексу
        
        Args:
            index: Индекс материала в списке
        """
        if 0 <= index < len(self.materials):
            self.materials.pop(index)
        else:
            raise IndexError("Неверный индекс материала")
    
    def get_materials_by_surface_type(self, surface_type: str) -> List[Material]:
        """
        Получить материалы по типу поверхности
        
        Args:
            surface_type: Тип поверхности
            
        Returns:
            Список материалов данного типа поверхности
        """
        return [material for material in self.materials if material.surface_type == surface_type]
    
    def get_total_area_by_material(self, material_name: str) -> float:
        """
        Получить общую площадь материала в помещении
        
        Args:
            material_name: Название материала
            
        Returns:
            Общая площадь материала в м²
        """
        total_area = 0
        for material in self.materials:
            if material.name == material_name:
                total_area += material.area
        return total_area
    
    def calculate_critical_frequency(self) -> float:
        """
        Рассчитать критическую частоту помещения
        
        Returns:
            Критическая частота в Гц
        """
        return 1770 / math.sqrt(self.volume)
    
    def calculate_equivalent_absorption_area(self, frequency: int) -> float:
        """
        Рассчитать эквивалентную площадь звукопоглощения для данной частоты (все материалы)
        
        Args:
            frequency: Частота в Гц
            
        Returns:
            Эквивалентная площадь звукопоглощения в м²
        """
        total_absorption = 0
        
        for material in self.materials:
            if frequency in material.absorption_coefficients:
                absorption_coefficient = material.absorption_coefficients[frequency]
                total_absorption += material.area * absorption_coefficient
        
        # Добавляем добавочное звукопоглощение в зависимости от частоты (от площади пола)
        if frequency <= 500:
            # Для низких частот (до 500 Гц включительно): 9%
            additional_absorption_coeff = 0.09
        else:
            # Для высоких частот (более 500 Гц): 5%
            additional_absorption_coeff = 0.05
            
        additional_absorption = additional_absorption_coeff * self.floor_area
        
        return total_absorption + additional_absorption
    
    def calculate_structural_absorption_area(self, frequency: int) -> float:
        """
        Рассчитать эквивалентную площадь звукопоглощения только ограждающих конструкций
        
        Args:
            frequency: Частота в Гц
            
        Returns:
            Эквивалентная площадь звукопоглощения ограждающих конструкций в м²
        """
        total_absorption = 0
        
        for material in self.materials:
            if material.category == "Ограждающие конструкции" and frequency in material.absorption_coefficients:
                absorption_coefficient = material.absorption_coefficients[frequency]
                total_absorption += material.area * absorption_coefficient
        
        # Добавляем добавочное звукопоглощение в зависимости от частоты (от площади пола)
        if frequency <= 500:
            # Для низких частот (до 500 Гц включительно): 9%
            additional_absorption_coeff = 0.09
        else:
            # Для высоких частот (более 500 Гц): 5%
            additional_absorption_coeff = 0.05
            
        additional_absorption = additional_absorption_coeff * self.floor_area
        
        return total_absorption + additional_absorption
        
    def calculate_acoustic_absorption_area(self, frequency: int) -> float:
        """
        Рассчитать эквивалентную площадь звукопоглощения только акустических конструкций
        
        Args:
            frequency: Частота в Гц
            
        Returns:
            Эквивалентная площадь звукопоглощения акустических конструкций в м²
        """
        total_absorption = 0
        
        for material in self.materials:
            if material.category == "Акустические конструкции" and frequency in material.absorption_coefficients:
                absorption_coefficient = material.absorption_coefficients[frequency]
                total_absorption += material.area * absorption_coefficient
        
        return total_absorption
        
    def get_effective_surface_area(self) -> float:
        """
        Рассчитать эффективную площадь поверхностей с учетом вычитания акустических материалов
        
        Returns:
            Эффективная площадь в м²
        """
        # Считаем площади акустических материалов по типам поверхностей
        acoustic_areas_by_surface = {}
        for material in self.materials:
            if material.category == "Акустические конструкции":
                surface_type = material.surface_type
                if surface_type not in acoustic_areas_by_surface:
                    acoustic_areas_by_surface[surface_type] = 0
                acoustic_areas_by_surface[surface_type] += material.area
        
        # Вычитаем площади акустических материалов из общей площади поверхностей
        total_acoustic_area = sum(acoustic_areas_by_surface.values())
        
        return self.total_surface_area #- total_acoustic_area
    
    def calculate_average_absorption_coefficient(self, frequency: int) -> float:
        """
        Рассчитать средний коэффициент звукопоглощения для данной частоты (все материалы)
        
        Args:
            frequency: Частота в Гц
            
        Returns:
            Средний коэффициент звукопоглощения
        """
        equivalent_absorption_area = self.calculate_equivalent_absorption_area(frequency)
        return min(equivalent_absorption_area / self.total_surface_area, 0.99)  # Ограничиваем 0.99
        
    def calculate_structural_average_absorption_coefficient(self, frequency: int) -> float:
        """
        Рассчитать средний коэффициент звукопоглощения только ограждающих конструкций
        
        Args:
            frequency: Частота в Гц
            
        Returns:
            Средний коэффициент звукопоглощения ограждающих конструкций
        """
        equivalent_absorption_area = self.calculate_structural_absorption_area(frequency)
        effective_surface_area = self.get_effective_surface_area()
        return min(equivalent_absorption_area / effective_surface_area, 0.99)  # Ограничиваем 0.99
        
    def calculate_combined_average_absorption_coefficient(self, frequency: int) -> float:
        """
        Рассчитать средний коэффициент звукопоглощения с учетом акустических материалов
        
        Args:
            frequency: Частота в Гц
            
        Returns:
            Средний коэффициент звукопоглощения с учетом акустических материалов
        """
        equivalent_absorption_area = self.calculate_equivalent_absorption_area(frequency)
        effective_surface_area = self.get_effective_surface_area()
        return min(equivalent_absorption_area / effective_surface_area, 0.99)  # Ограничиваем 0.99
    
    def __str__(self) -> str:
        """Строковое представление помещения"""
        return f"Помещение '{self.name}' ({self.purpose}): {self.length}×{self.width}×{self.height} м, V={self.volume:.2f} м³"
    
    def __repr__(self) -> str:
        """Представление для отладки"""
        return f"Room(name='{self.name}', purpose='{self.purpose}', length={self.length}, width={self.width}, height={self.height})"
