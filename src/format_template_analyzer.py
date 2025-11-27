"""
Format Template Analyzer - Analyse et reproduit la structure d'une description existante
Permet de garder le même format pour régénérer des descriptions similaires
"""
import re
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)


class FormatTemplateAnalyzer:
    """Analyse la structure d'une description pour en reproduire le format"""
    
    def __init__(self):
        self.format_patterns = {
            'bullet_list': r'^[\s]*[•\-\*]\s+',
            'numbered_list': r'^[\s]*\d+\.\s+',
            'bold': r'\*\*(.+?)\*\*|\<b\>(.+?)\</b\>',
            'section_header': r'^#{1,6}\s+',
            'paragraph': r'^[A-Z][^\.!?]*[\.!?]',
        }
    
    def analyze_structure(self, text: str) -> Dict:
        """
        Analyse la structure d'un texte et retourne ses caractéristiques
        """
        lines = text.strip().split('\n')
        
        structure = {
            'total_words': len(text.split()),
            'total_chars': len(text),
            'total_sentences': len(re.findall(r'[\.!?]', text)),
            'total_lines': len(lines),
            'sections': self._extract_sections(text),
            'has_bullet_lists': self._has_bullet_lists(text),
            'has_numbered_lists': self._has_numbered_lists(text),
            'has_bold': bool(re.search(self.format_patterns['bold'], text)),
            'has_html_tags': bool(re.search(r'<b>|</b>|<i>|</i>|<u>|</u>', text)),
            'lines_breakdown': self._analyze_lines(lines),
            'format_elements': self._extract_format_elements(text),
        }
        
        return structure
    
    def _extract_sections(self, text: str) -> List[Dict]:
        """Extrait les sections du texte"""
        sections = []
        lines = text.split('\n')
        current_section = None
        
        for i, line in enumerate(lines):
            if line.startswith('#'):
                if current_section:
                    sections.append(current_section)
                current_section = {
                    'title': line.lstrip('#').strip(),
                    'start_line': i,
                    'content': []
                }
            elif current_section is not None:
                if line.strip():
                    current_section['content'].append(line)
                else:
                    if current_section:
                        current_section['end_line'] = i
                        sections.append(current_section)
                        current_section = None
        
        if current_section:
            current_section['end_line'] = len(lines)
            sections.append(current_section)
        
        return sections
    
    def _has_bullet_lists(self, text: str) -> bool:
        """Vérifie la présence de listes à puces"""
        return bool(re.search(self.format_patterns['bullet_list'], text, re.MULTILINE))
    
    def _has_numbered_lists(self, text: str) -> bool:
        """Vérifie la présence de listes numérotées"""
        return bool(re.search(self.format_patterns['numbered_list'], text, re.MULTILINE))
    
    def _analyze_lines(self, lines: List[str]) -> Dict:
        """Analyse la répartition des lignes"""
        breakdown = {
            'short_lines': 0,      # < 50 chars
            'medium_lines': 0,     # 50-150 chars
            'long_lines': 0,       # > 150 chars
            'empty_lines': 0,
            'list_items': 0,
            'total_non_empty': 0,
        }
        
        for line in lines:
            if not line.strip():
                breakdown['empty_lines'] += 1
            else:
                breakdown['total_non_empty'] += 1
                length = len(line)
                if length < 50:
                    breakdown['short_lines'] += 1
                elif length < 150:
                    breakdown['medium_lines'] += 1
                else:
                    breakdown['long_lines'] += 1
                
                if re.match(r'^\s*[•\-\*]', line):
                    breakdown['list_items'] += 1
        
        return breakdown
    
    def _extract_format_elements(self, text: str) -> List[str]:
        """Extrait les éléments de formatage utilisés"""
        elements = []
        
        if '**' in text or '<b>' in text:
            elements.append('bold')
        if '_' in text or '<i>' in text:
            elements.append('italic')
        if '•' in text:
            elements.append('bullet_list')
        if re.search(r'\d+\.\s', text):
            elements.append('numbered_list')
        if '\n' in text and text.count('\n') > 5:
            elements.append('multiline')
        if '<' in text and '>' in text:
            elements.append('html_tags')
        
        return elements
    
    def generate_format_prompt(self, structure: Dict, product_url: str = "", product_name: str = "") -> str:
        """
        Génère un prompt pour régénérer une description avec le même format
        """
        prompt = f"""Régénère une description de produit moto en respectant EXACTEMENT cette structure:

📊 STRUCTURE À RESPECTER:
- Nombre de mots: {structure['total_words']} (±10%)
- Nombre de phrases: {structure['total_sentences']}
- Nombre de lignes: {structure['total_lines']}

🎨 FORMATAGE À CONSERVER:
"""
        
        if 'bold' in structure['format_elements']:
            prompt += "- Utiliser **gras** pour les éléments importants\n"
        if 'bullet_list' in structure['format_elements']:
            prompt += "- Utiliser des listes à puces (•) pour les caractéristiques\n"
        if 'numbered_list' in structure['format_elements']:
            prompt += "- Utiliser des listes numérotées\n"
        if 'html_tags' in structure['format_elements']:
            prompt += "- Utiliser <b>texte</b> pour les mises en gras importantes (homologué/non homologué)\n"
        if 'multiline' in structure['format_elements']:
            prompt += "- Organiser le texte sur plusieurs lignes avec des séparations claires\n"
        
        if structure['sections']:
            prompt += "\n📋 SECTIONS À MAINTENIR:\n"
            for i, section in enumerate(structure['sections'], 1):
                prompt += f"{i}. {section['title']} ({len(section.get('content', []))} lignes)\n"
        
        if product_url:
            prompt += f"\n🔗 RÉFÉRENCE PRODUIT: {product_url}"
        if product_name:
            prompt += f"\n📦 NOM PRODUIT: {product_name}"
        
        prompt += "\n\nRégénère maintenant la description en respectant EXACTEMENT ce format:"
        
        return prompt
    
    def compare_structures(self, original: str, regenerated: str) -> Dict:
        """Compare deux descriptions pour vérifier la conformité du format"""
        original_struct = self.analyze_structure(original)
        regen_struct = self.analyze_structure(regenerated)
        
        comparison = {
            'word_count_diff': abs(regen_struct['total_words'] - original_struct['total_words']),
            'word_count_percent': (abs(regen_struct['total_words'] - original_struct['total_words']) / original_struct['total_words'] * 100) if original_struct['total_words'] > 0 else 0,
            'format_match': {
                'bold': regen_struct['has_bold'] == original_struct['has_bold'],
                'bullet_lists': regen_struct['has_bullet_lists'] == original_struct['has_bullet_lists'],
                'numbered_lists': regen_struct['has_numbered_lists'] == original_struct['has_numbered_lists'],
                'html_tags': regen_struct['has_html_tags'] == original_struct['has_html_tags'],
            },
            'format_compliance_score': self._calculate_compliance_score(original_struct, regen_struct),
            'recommendations': self._generate_recommendations(original_struct, regen_struct),
        }
        
        return comparison
    
    def _calculate_compliance_score(self, original: Dict, regenerated: Dict) -> float:
        """Calcule un score de conformité au format (0-100)"""
        score = 100.0
        
        # Vérifier la longueur
        word_diff_percent = abs(regenerated['total_words'] - original['total_words']) / original['total_words'] * 100 if original['total_words'] > 0 else 0
        if word_diff_percent > 20:
            score -= min(30, word_diff_percent / 2)
        elif word_diff_percent > 10:
            score -= min(15, word_diff_percent)
        
        # Vérifier les éléments de formatage
        format_diff = 0
        if regenerated['has_bold'] != original['has_bold']:
            format_diff += 1
        if regenerated['has_bullet_lists'] != original['has_bullet_lists']:
            format_diff += 1
        if regenerated['has_numbered_lists'] != original['has_numbered_lists']:
            format_diff += 1
        if regenerated['has_html_tags'] != original['has_html_tags']:
            format_diff += 1
        
        score -= format_diff * 15
        
        return max(0, min(100, score))
    
    def _generate_recommendations(self, original: Dict, regenerated: Dict) -> List[str]:
        """Génère des recommandations pour améliorer la conformité"""
        recommendations = []
        
        word_diff_percent = abs(regenerated['total_words'] - original['total_words']) / original['total_words'] * 100 if original['total_words'] > 0 else 0
        if word_diff_percent > 15:
            if regenerated['total_words'] > original['total_words']:
                recommendations.append(f"❌ Trop long: {regenerated['total_words']} mots au lieu de {original['total_words']}")
            else:
                recommendations.append(f"❌ Trop court: {regenerated['total_words']} mots au lieu de {original['total_words']}")
        
        if regenerated['has_bold'] != original['has_bold']:
            recommendations.append("❌ Formatage gras manquant ou différent")
        
        if regenerated['has_bullet_lists'] != original['has_bullet_lists']:
            recommendations.append("❌ Listes à puces manquantes ou différentes")
        
        if not recommendations:
            recommendations.append("✅ Format respecté!")
        
        return recommendations
