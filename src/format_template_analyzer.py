"""
Format Template Analyzer - Analyse et reproduit la structure d'une description existante
Permet de garder le même format pour régénérer des descriptions similaires
Supporte les formats: Markdown, HTML avec <div>, <span> et styles inline
"""
import re
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)


class FormatTemplateAnalyzer:
    """Analyse la structure d'une description pour en reproduire le format"""
    
    def __init__(self):
        self.format_patterns = {
            'div_blocks': r'<div[^>]*>',
            'span_bold': r'<span\s+style="font-weight:\s*bold;">',
            'bullet_list': r'^[\s]*[•\-\*]\s+',
            'numbered_list': r'^[\s]*\d+\.\s+',
            'html_bold': r'<b>|<strong>',
            'section_header': r'^#{1,6}\s+',
        }
    
    def analyze_structure(self, text: str) -> Dict:
        """
        Analyse la structure d'un texte (HTML ou Markdown) et retourne ses caractéristiques
        """
        # Nettoyer le HTML pour compter les mots
        clean_text = self._strip_html(text)
        lines = text.strip().split('\n')
        
        structure = {
            'total_words': len(clean_text.split()),
            'total_chars': len(clean_text),
            'total_sentences': len(re.findall(r'[\.!?]', clean_text)),
            'total_lines': len(lines),
            'sections': self._extract_sections(text),
            'has_bullet_lists': self._has_bullet_lists(text),
            'has_numbered_lists': self._has_numbered_lists(text),
            'has_html_divs': self._has_html_divs(text),
            'has_span_bold': self._has_span_bold(text),
            'has_ul_lists': '<ul>' in text,
            'has_markdown_bold': '**' in text or '__' in text,
            'format_type': self._detect_format_type(text),
            'format_elements': self._extract_format_elements(text),
        }
        
        return structure
    
    def _strip_html(self, text: str) -> str:
        """Supprime les balises HTML pour le comptage de mots"""
        # Enlever les balises HTML
        text = re.sub(r'<[^>]+>', '', text)
        # Enlever les entités HTML
        text = re.sub(r'&[^;]+;', '', text)
        return text.strip()
    
    def _detect_format_type(self, text: str) -> str:
        """Détecte le type de format utilisé"""
        if '<div' in text or '<span' in text or '<ul>' in text:
            return 'html'
        elif '**' in text or '__' in text or '#' in text:
            return 'markdown'
        else:
            return 'plain'
    
    def _extract_sections(self, text: str) -> List[Dict]:
        """Extrait les sections du texte"""
        sections = []
        
        # Pour HTML: extraire les <div> avec contenu important
        if '<div' in text:
            div_blocks = re.findall(r'<div[^>]*>(.*?)</div>', text, re.DOTALL)
            for i, block in enumerate(div_blocks):
                clean = self._strip_html(block).strip()
                if clean and len(clean) > 10:
                    sections.append({
                        'title': f'Section {i+1}',
                        'content': clean,
                        'original_html': f'<div>{block}</div>'
                    })
        else:
            # Pour Markdown: chercher les headers
            lines = text.split('\n')
            current_section = None
            for i, line in enumerate(lines):
                if line.startswith('#'):
                    if current_section:
                        sections.append(current_section)
                    current_section = {
                        'title': line.lstrip('#').strip(),
                        'content': [],
                    }
                elif current_section is not None and line.strip():
                    current_section['content'].append(line)
            
            if current_section:
                sections.append(current_section)
        
        return sections
    
    def _has_bullet_lists(self, text: str) -> bool:
        """Vérifie la présence de listes à puces"""
        return bool(re.search(self.format_patterns['bullet_list'], text, re.MULTILINE)) or '<ul>' in text
    
    def _has_numbered_lists(self, text: str) -> bool:
        """Vérifie la présence de listes numérotées"""
        return bool(re.search(self.format_patterns['numbered_list'], text, re.MULTILINE)) or '<ol>' in text
    
    def _has_html_divs(self, text: str) -> bool:
        """Vérifie la présence de divs HTML"""
        return '<div' in text
    
    def _has_span_bold(self, text: str) -> bool:
        """Vérifie la présence de <span> avec style bold"""
        return 'style="font-weight' in text or "style='font-weight" in text
    
    def _extract_format_elements(self, text: str) -> List[str]:
        """Extrait les éléments de formatage utilisés"""
        elements = []
        
        if '<div' in text:
            elements.append('html_divs')
        if 'style="font-weight' in text or "style='font-weight" in text:
            elements.append('span_bold')
        if '<b>' in text or '<strong>' in text:
            elements.append('html_bold')
        if '<ul>' in text:
            elements.append('unordered_list')
        if '<ol>' in text:
            elements.append('ordered_list')
        if '<li>' in text:
            elements.append('list_items')
        if '**' in text or '__' in text:
            elements.append('markdown_bold')
        if '#' in text and text.count('#') > 2:
            elements.append('markdown_headers')
        if '•' in text or '- ' in text:
            elements.append('markdown_bullets')
        
        return elements if elements else ['plain_text']
    
    def generate_format_prompt(self, structure: Dict, product_url: str = "", product_name: str = "") -> str:
        """
        Génère un prompt pour régénérer une description avec le même format
        """
        format_type = structure.get('format_type', 'plain')
        
        prompt = f"""Régénère une description de produit moto en respectant EXACTEMENT cette structure:

📊 STRUCTURE À RESPECTER:
- Nombre de mots: {structure['total_words']} (±10%)
- Nombre de phrases: {structure['total_sentences']}
- Type de format: {format_type.upper()}

🎨 FORMATAGE À CONSERVER EXACTEMENT:
"""
        
        if format_type == 'html':
            prompt += """- Utiliser des <div></div> pour les blocs de texte
- Utiliser <span style="font-weight: bold;">texte</span> pour les mots importants
- Utiliser <ul><li>...</li></ul> pour les listes à puces
- Conserver les <br> pour les séparations
- Format: HTML avec balises de style
"""
        elif format_type == 'markdown':
            if 'span_bold' in structure.get('format_elements', []):
                prompt += "- Utiliser <span style=\"font-weight: bold;\">texte</span> pour les éléments importants\n"
            else:
                prompt += "- Utiliser **gras** pour les éléments importants\n"
            
            if 'unordered_list' in structure.get('format_elements', []):
                prompt += "- Utiliser <ul><li>...</li></ul> pour les listes\n"
            else:
                prompt += "- Utiliser des listes à puces (•) pour les caractéristiques\n"
        
        if structure.get('has_ul_lists'):
            prompt += "- Format des listes: <ul><li>élément 1</li><li>élément 2</li></ul>\n"
        
        if structure['sections']:
            prompt += "\n📋 SECTIONS À MAINTENIR:\n"
            for i, section in enumerate(structure['sections'], 1):
                title = section.get('title', f'Section {i}')
                prompt += f"{i}. {title}\n"
        
        # N'inclure que le nom du produit, PAS le lien
        if product_name:
            prompt += f"\n📦 PRODUIT: {product_name}"
        
        prompt += "\n\n⚠️ RÈGLES ESSENTIELLES:\n- PAS DE LIEN OU URL\n- PAS D'EN-TÊTES ARTIFICIELS (style \"Avantage :\", \"Fonctionnalité :\")\n- TEXTE NATUREL ET FLUIDE\n\nRégénère maintenant la description en respectant EXACTEMENT ce format."
        
        return prompt
    
    def compare_structures(self, original: str, regenerated: str) -> Dict:
        """Compare deux descriptions pour vérifier la conformité du format"""
        original_struct = self.analyze_structure(original)
        regen_struct = self.analyze_structure(regenerated)
        
        comparison = {
            'word_count_diff': abs(regen_struct['total_words'] - original_struct['total_words']),
            'word_count_percent': (abs(regen_struct['total_words'] - original_struct['total_words']) / original_struct['total_words'] * 100) if original_struct['total_words'] > 0 else 0,
            'format_type_match': original_struct['format_type'] == regen_struct['format_type'],
            'format_match': {
                'html_divs': regen_struct['has_html_divs'] == original_struct['has_html_divs'],
                'span_bold': regen_struct['has_span_bold'] == original_struct['has_span_bold'],
                'lists': regen_struct['has_ul_lists'] == original_struct['has_ul_lists'],
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
        
        # Vérifier le type de format
        if regenerated['format_type'] != original['format_type']:
            score -= 25
        
        # Vérifier les éléments de formatage
        format_diff = 0
        if regenerated['has_html_divs'] != original['has_html_divs']:
            format_diff += 1
        if regenerated['has_span_bold'] != original['has_span_bold']:
            format_diff += 1
        if regenerated['has_ul_lists'] != original['has_ul_lists']:
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
        
        if regenerated['format_type'] != original['format_type']:
            recommendations.append(f"❌ Format incorrect: {regenerated['format_type']} au lieu de {original['format_type']}")
        
        if regenerated['has_html_divs'] != original['has_html_divs']:
            if original['has_html_divs']:
                recommendations.append("❌ Manque les balises <div> pour les blocs")
        
        if regenerated['has_span_bold'] != original['has_span_bold']:
            if original['has_span_bold']:
                recommendations.append("❌ Manque le formatage <span style=\"font-weight: bold;\"> pour les éléments importants")
        
        if regenerated['has_ul_lists'] != original['has_ul_lists']:
            if original['has_ul_lists']:
                recommendations.append("❌ Manque les listes <ul><li>...</li></ul>")
        
        if not recommendations:
            recommendations.append("✅ Format respecté!")
        
        return recommendations
