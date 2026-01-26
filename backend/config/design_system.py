"""
DESIGN SYSTEM - REVISAR.IA / DUREZZA / FACTURAR.IA
Configuración centralizada de todos los elementos de diseño
"""

COLORES = {
    'primary': {
        'cyan': {
            '50': '#ECFEFF',
            '100': '#CFFAFE',
            '200': '#A5F3FC',
            '300': '#67E8F9',
            '400': '#22D3EE',
            '500': '#06B6D4',
            '600': '#0891B2',
            '700': '#0E7490',
            '800': '#155E75',
            '900': '#164E63',
        },
        'default': '#0891B2',
        'hover': '#0E7490',
        'light': '#22D3EE',
    },
    'secondary': {
        'green': {
            '400': '#34D399',
            '500': '#10B981',
            '600': '#059669',
        },
        'yellow': {
            '400': '#FBBF24',
            '500': '#F59E0B',
            '600': '#D97706',
        },
        'red': {
            '400': '#F87171',
            '500': '#EF4444',
            '600': '#DC2626',
        },
    },
    'neutral': {
        '50': '#F9FAFB',
        '100': '#F3F4F6',
        '200': '#E5E7EB',
        '300': '#D1D5DB',
        '400': '#9CA3AF',
        '500': '#6B7280',
        '600': '#4B5563',
        '700': '#374151',
        '800': '#1F2937',
        '900': '#111827',
        '950': '#030712',
    },
    'background': {
        'dark': '#0F172A',
        'card': '#1E293B',
        'elevated': '#334155',
    },
    'states': {
        'success': '#10B981',
        'warning': '#F59E0B',
        'error': '#EF4444',
        'info': '#0891B2',
    }
}

COLORES_PROHIBIDOS = [
    '#FF0000',
    '#00FF00',
    '#0000FF',
    '#FFFF00',
    '#FF00FF',
    '#00FFFF',
    'red', 'green', 'blue', 'yellow',
]

TIPOGRAFIAS = {
    'principal': {
        'familia': 'Inter',
        'fallback': 'system-ui, -apple-system, sans-serif',
        'weights': [400, 500, 600, 700],
        'uso': 'Textos generales, UI, títulos'
    },
    'codigo': {
        'familia': 'JetBrains Mono',
        'fallback': 'Consolas, Monaco, monospace',
        'weights': [400, 500],
        'uso': 'Código, datos técnicos, RFCs, montos'
    },
    'display': {
        'familia': 'Inter',
        'fallback': 'system-ui, sans-serif',
        'weights': [700, 800],
        'uso': 'Headlines grandes, marketing'
    }
}

TAMANOS_TEXTO = {
    'xs': '0.75rem',
    'sm': '0.875rem',
    'base': '1rem',
    'lg': '1.125rem',
    'xl': '1.25rem',
    '2xl': '1.5rem',
    '3xl': '1.875rem',
    '4xl': '2.25rem',
}

ESPACIADO = {
    '0': '0',
    '1': '0.25rem',
    '2': '0.5rem',
    '3': '0.75rem',
    '4': '1rem',
    '5': '1.25rem',
    '6': '1.5rem',
    '8': '2rem',
    '10': '2.5rem',
    '12': '3rem',
    '16': '4rem',
}

BORDES = {
    'radius': {
        'none': '0',
        'sm': '0.25rem',
        'default': '0.5rem',
        'md': '0.75rem',
        'lg': '1rem',
        'xl': '1.5rem',
        'full': '9999px',
    },
    'width': {
        'default': '1px',
        'thick': '2px',
    }
}

BREAKPOINTS = {
    'xs': '320px',
    'sm': '640px',
    'md': '768px',
    'lg': '1024px',
    'xl': '1280px',
    '2xl': '1536px',
}

REGLAS_RESPONSIVE = {
    'touch_target_min': '44px',
    'font_size_min_mobile': '14px',
    'padding_mobile': '16px',
    'max_width_content': '1280px',
}

COMPONENTES = {
    'button': {
        'padding': '0.75rem 1.5rem',
        'border_radius': '0.5rem',
        'font_weight': '600',
        'min_height': '44px',
        'variantes': ['primary', 'secondary', 'outline', 'ghost', 'danger']
    },
    'input': {
        'padding': '0.75rem 1rem',
        'border_radius': '0.5rem',
        'border_color': COLORES['neutral']['600'],
        'focus_color': COLORES['primary']['default'],
        'min_height': '44px',
    },
    'card': {
        'padding': '1.5rem',
        'border_radius': '0.75rem',
        'background': COLORES['background']['card'],
        'border': f"1px solid {COLORES['neutral']['700']}",
    },
    'modal': {
        'padding': '1.5rem',
        'border_radius': '1rem',
        'max_width': '32rem',
        'backdrop': 'rgba(0, 0, 0, 0.8)',
    }
}

ANIMACIONES = {
    'duracion': {
        'fast': '150ms',
        'normal': '300ms',
        'slow': '500ms',
    },
    'easing': {
        'default': 'cubic-bezier(0.4, 0, 0.2, 1)',
        'in': 'cubic-bezier(0.4, 0, 1, 1)',
        'out': 'cubic-bezier(0, 0, 0.2, 1)',
        'bounce': 'cubic-bezier(0.68, -0.55, 0.265, 1.55)',
    }
}

ICONOS = {
    'libreria': 'Lucide React',
    'fallback': 'Heroicons',
    'tamano_default': '20px',
    'tamano_small': '16px',
    'tamano_large': '24px',
}

ACCESIBILIDAD = {
    'contraste_minimo': 4.5,
    'contraste_grande': 3.0,
    'focus_visible': True,
    'reducir_movimiento': True,
}
