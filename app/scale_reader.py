import random
import re

class ScaleReader:
    def __init__(self):
        self.scales = {
            'scale_1': {'name': 'Main Gate Scale', 'port': 'COM3'},
            'scale_2': {'name': 'Secondary Scale', 'port': 'COM4'},
            'scale_3': {'name': 'Processing Scale', 'port': 'COM5'},
            'scale_4': {'name': 'Weighbridge Scale', 'port': 'COM6'}
        }
    
    def read_weight(self, scale_id='scale_1'):
        """Mock weight reading - replace with actual serial when hardware is available"""
        # Return a random weight between 0.5 and 100 kg for testing
        return round(random.uniform(0.5, 100.0), 2)
    
    def read_all_scales(self):
        """Read from all scales"""
        results = {}
        for scale_id in self.scales:
            results[scale_id] = {
                'weight': self.read_weight(scale_id),
                'name': self.scales[scale_id]['name']
            }
        return results
    
    def get_available_ports(self):
        """Get available COM ports - mock for now"""
        return [{'port': 'COM3', 'description': 'Mock Scale 1'},
                {'port': 'COM4', 'description': 'Mock Scale 2'},
                {'port': 'COM5', 'description': 'Mock Scale 3'},
                {'port': 'COM6', 'description': 'Mock Scale 4'}]

def get_mock_weight():
    """Generate mock weight for testing"""
    return round(random.uniform(0.5, 100.0), 2)

# Create global instance
scale_reader = ScaleReader()
