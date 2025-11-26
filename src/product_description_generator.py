"""
Générateur de descriptions produits SEO-optimisées pour Motoblouz
Utilise Ollama pour générer des descriptions attractives et optimisées pour le référencement
"""
import logging
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

from .ollama_client import OllamaClient
from .openai_client import OpenAIClient
from .ai_client_factory import AIClientFactory
from .seo_cache import SEOCache
from .template_seo_manager import TemplateSEOManager
from .web_search import WebSearchEnricher

logger = logging.getLogger(__name__)


class ProductDescriptionGenerator:
    """Génère des descriptions produits SEO-friendly avec Ollama"""
    
    # Mots-clés et thématiques Motoblouz
    MOTOBLOUZ_KEYWORDS = {
        "moto": ["moto", "motard", "pilote", "rider", "biker", "deux-roues"],
        "sécurité": ["sécurité", "protection", "homologué", "certifié", "résistant", "protecteur"],
        "style": ["style", "design", "look", "élégant", "moderne", "tendance"],
        "confort": ["confort", "ergonomique", "ajustable", "respirant", "léger"],
        "performance": ["performance", "qualité", "technique", "innovant", "efficace"],
        "saisons": ["été", "hiver", "mi-saison", "toutes saisons", "4 saisons"]
    }
    
    # Templates de structure SEO
    SEO_TEMPLATES = {
        "casque": """Rédige une description produit SEO-optimisée pour ce casque moto.

Informations produit:
{product_info}

Structure attendue (150-200 mots):
1. Accroche (2 lignes): Présente le casque avec ses atouts principaux
2. Caractéristiques techniques (3-4 lignes): Matériaux, homologations, technologie
3. Confort et utilisation (2-3 lignes): Ventilation, poids, visière, intérieur
4. Style et design (1-2 lignes): Esthétique, couleurs, finitions
5. Appel à l'action (1 ligne): Incite à l'achat

Mots-clés à intégrer naturellement: casque moto, protection, homologué, confort, sécurité routière
Ton: Professionnel, rassurant, enthousiaste
Public: Motards passionnés, exigeants sur la qualité""",

        "blouson": """Rédige une description produit SEO-optimisée pour ce blouson/veste moto.

Informations produit:
{product_info}

Structure attendue (150-200 mots):
1. Accroche (2 lignes): Présente le blouson et son usage principal
2. Protection (3-4 lignes): Coques, renforts, matériaux résistants, homologations
3. Confort et adaptabilité (2-3 lignes): Doublures, aérations, réglages, poches
4. Polyvalence (1-2 lignes): Saisons, types de trajets, imperméabilité
5. Appel à l'action (1 ligne)

Mots-clés: blouson moto, veste moto, protection pilote, équipement moto, textile/cuir
Ton: Expert, rassurant, accessible
Public: Motards urbains et routiers""",

        "gants": """Rédige une description produit SEO-optimisée pour ces gants moto.

Informations produit:
{product_info}

Structure attendue (120-150 mots):
1. Accroche (2 lignes): Type de gants et utilisation idéale
2. Protection et sécurité (2-3 lignes): Coques, renforts, homologation
3. Confort et dextérité (2-3 lignes): Matériaux, préhension, sensations
4. Usage et saison (1-2 lignes): Conditions optimales d'utilisation
5. Appel à l'action (1 ligne)

Mots-clés: gants moto, protection mains, homologué, confort pilote
Ton: Précis, technique, accessible
Public: Tous motards""",

        "accessoire": """Rédige une description produit SEO-optimisée pour cet accessoire moto.

Informations produit:
{product_info}

Structure attendue (100-150 mots):
1. Présentation (2 lignes): Qu'est-ce que c'est et à quoi ça sert
2. Avantages pratiques (2-3 lignes): Utilité, facilité d'usage
3. Compatibilité (1-2 lignes): Avec quoi/qui ça fonctionne
4. Qualité et durabilité (1-2 lignes): Matériaux, robustesse
5. Appel à l'action (1 ligne)

Mots-clés: accessoire moto, équipement motard, pratique, qualité
Ton: Utile, direct, convainquant
Public: Tous motards""",

        "default": """Rédige une description produit SEO-optimisée pour cet équipement moto.

Informations produit:
{product_info}

Structure attendue (150-200 mots):
1. Accroche captivante (2 lignes)
2. Caractéristiques principales (3-4 lignes)
3. Avantages pour le motard (2-3 lignes)
4. Utilisation et contexte (1-2 lignes)
5. Conclusion et appel à l'action (1 ligne)

Mots-clés: équipement moto, protection motard, qualité, sécurité, confort
Ton: Professionnel, enthousiaste, informatif
Public: Motards passionnés"""
    }
    
    def __init__(
        self, 
        ollama_client: Optional[OllamaClient] = None,
        openai_client: Optional[OpenAIClient] = None,
        use_cache: bool = True,
        provider: str = "openai",  # "openai" ou "ollama"
        use_web_search: bool = True  # Activer recherche web
    ):
        """
        Initialise le générateur
        
        Args:
            ollama_client: Client Ollama (créé automatiquement si None)
            openai_client: Client OpenAI (créé automatiquement si None)
            use_cache: Activer le cache des descriptions (défaut: True)
            provider: Provider à utiliser ("openai" ou "ollama")
            use_web_search: Enrichir avec recherche web (défaut: True)
        """
        self.provider = provider.lower()
        
        # Initialiser le client approprié via la Factory
        if self.provider == "openai":
            self.client = openai_client or AIClientFactory.get_client("openai")
            logger.info(f"🤖 Utilisation d'OpenAI: {self.client.model if self.client else 'N/A'}")
        else:
            self.client = ollama_client or AIClientFactory.get_client("ollama")
            logger.info(f"🤖 Utilisation d'Ollama: {self.client.model if self.client else 'N/A'}")
        
        # Compatibilité: garder self.ollama pour le code existant
        self.ollama = self.client
        
        self.cache = SEOCache() if use_cache else None
        self.template_manager = TemplateSEOManager()
        
        # Recherche web pour enrichissement
        self.use_web_search = use_web_search
        self.web_searcher = WebSearchEnricher() if use_web_search else None
        
        if not self.client.is_available():
            logger.warning(f"⚠️ {self.provider.upper()} non disponible - génération désactivée")
        
        if self.cache:
            stats = self.cache.stats()
            logger.info(f"💾 Cache SEO activé: {stats['total_entries']} entrées ({stats['cache_size_kb']:.1f} KB)")
        
        if self.use_web_search:
            logger.info("🌐 Recherche web activée pour enrichissement des descriptions")
    
    def is_available(self) -> bool:
        """Vérifie si le générateur est opérationnel"""
        return self.client.is_available()
    
    def _detect_product_category(self, product_data: Dict) -> str:
        """
        Détecte la catégorie du produit pour adapter le template
        
        Args:
            product_data: Données du produit
            
        Returns:
            Catégorie détectée
        """
        # Cherche dans les champs pertinents
        text_to_analyze = ""
        
        for key in ['designation', 'description', 'categorie', 'famille', 'type', 'Libellé', 'Catégorie']:
            if key in product_data and product_data[key]:
                text_to_analyze += str(product_data[key]).lower() + " "
        
        text_to_analyze = text_to_analyze.lower()
        
        # Détection par mots-clés
        if any(kw in text_to_analyze for kw in ['casque', 'helmet', 'casco']):
            return "casque"
        elif any(kw in text_to_analyze for kw in ['blouson', 'veste', 'jacket', 'giubbotto', 'giacca']):
            return "blouson"
        elif any(kw in text_to_analyze for kw in ['gant', 'glove', 'guanto']):
            return "gants"
        elif any(kw in text_to_analyze for kw in ['botte', 'chaussure', 'boot', 'stivale']):
            return "chaussures"
        elif any(kw in text_to_analyze for kw in ['pantalon', 'jean', 'pant', 'pantalone']):
            return "pantalon"
        elif any(kw in text_to_analyze for kw in ['échappement', 'silencieux', 'pot', 'exhaust', 'muffler']):
            return "echappement"
        elif any(kw in text_to_analyze for kw in ['pare', 'protection', 'bouclier', 'shield', 'heat']):
            return "protection"
        elif any(kw in text_to_analyze for kw in ['filtre', 'filter', 'air']):
            return "filtration"
        else:
            return "accessoire"
    
    def _get_related_products(self, category: str) -> str:
        """
        Retourne les suggestions de produits complémentaires selon la catégorie
        
        Args:
            category: Catégorie du produit
            
        Returns:
            Texte de suggestions ou chaîne vide
        """
        suggestions = {
            "casque": "un écran teinté, une paire de gants et un système de communication Bluetooth",
            "blouson": "un pantalon assorti, des protections dorsales renforcées et des gants",
            "gants": "un blouson compatible et un système de chauffage pour l'hiver",
            "chaussures": "des chaussettes techniques et un pantalon adapté",
            "pantalon": "un blouson coordonné, des genouillères et des bottes",
            "echappement": "un DB-killer homologué, un pare-chaleur et un filtre à air performance",
            "protection": "un échappement compatible et des fixations renforcées",
            "filtration": "un kit d'entretien et un nettoyant spécifique",
            "accessoire": "d'autres accessoires de la même gamme"
        }
        
        return suggestions.get(category, "des produits complémentaires de notre gamme")
    
    def _create_enhanced_context(self, product_data: Dict, category: str) -> str:
        """
        Crée un contexte enrichi basé sur la marque, catégorie et type de produit
        Utilise les connaissances générales pour guider l'IA
        """
        marque = product_data.get('Marque', '').upper()
        ref = product_data.get('Référence', '')
        
        # Contexte spécifique par marque et catégorie
        contexts = {
            'ARROW': {
                'pare-chaleur': "ARROW est reconnu pour ses échappements et accessoires racing de haute qualité. Leurs pare-chaleurs en carbone offrent une protection thermique optimale tout en réduisant le poids.",
                'echappement': "ARROW propose des échappements sportifs homologués, réputés pour leur son caractéristique et leurs gains de performance.",
                'silencieux': "Les silencieux ARROW allient performance et légalité, avec des matériaux nobles comme le carbone et le titane."
            },
            'BMW': {
                'valve': "BMW Motorrad utilise des composants d'origine de haute précision pour garantir la fiabilité de leurs moteurs boxer et parallèle twin.",
                'accessoire': "Les accessoires BMW Motorrad sont conçus spécifiquement pour chaque modèle, avec une intégration parfaite.",
                'protection': "BMW mise sur des protections robustes et durables, testées dans des conditions extrêmes."
            },
            'HONDA': {
                'pare-chaleur': "Honda équipe ses modèles sportifs de pare-chaleurs efficaces pour protéger contre la chaleur des catalyseurs haute température.",
                'accessoire': "Les pièces d'origine Honda assurent un ajustement parfait et une durabilité éprouvée.",
                'protection': "Honda privilégie des matériaux résistants à la corrosion pour une longévité maximale."
            },
            'AKRAPOVIC': {
                'echappement': "Akrapovič est la référence mondiale en échappements racing, utilisés en MotoGP et Superbike.",
                'silencieux': "Les silencieux Akrapovič en titane offrent un rapport poids/performance exceptionnel.",
                'pare-chaleur': "Les protections thermiques Akrapovič utilisent des matériaux haute technologie issus de la compétition."
            }
        }
        
        # Récupérer le contexte approprié
        context = ""
        if marque in contexts:
            category_lower = category.lower()
            brand_contexts = contexts[marque]
            
            # Chercher une correspondance exacte ou partielle
            for key, value in brand_contexts.items():
                if key in category_lower or category_lower in key:
                    context = f"\n💡 CONTEXTE EXPERT: {value}"
                    break
            
            # Si pas de match spécifique, prendre le premier disponible
            if not context and brand_contexts:
                context = f"\n💡 CONTEXTE EXPERT: {list(brand_contexts.values())[0]}"
        
        # Ajouter info sur la référence si format spécial
        if ref and len(ref) > 5:
            context += f"\nRéférence {marque}: {ref}"
        
        return context
    
    def _extract_product_info(self, product_data: Dict) -> str:
        """
        Extrait et formate les informations produit pertinentes (SANS PRIX)
        
        Args:
            product_data: Dictionnaire avec les données produit
            
        Returns:
            Texte formaté des infos produit
        """
        info_lines = []
        
        # Champs prioritaires (caractéristiques techniques uniquement)
        priority_fields = [
            'Référence', 'Libellé', 'Descriptif', 'Code barre',
            'Catégorie', 'Marque', 'Modèle', 'Couleur', 
            'Matière', 'Taille'
        ]
        
        # Champs à EXCLURE (prix, stocks, etc.)
        excluded_fields = [
            'Prix', 'prix', 'Price', 'price', 'HT', 'TTC', 
            'Stock', 'stock', 'Quantité', 'quantité',
            'Unnamed', 'Image'
        ]
        
        # Ajouter les champs prioritaires
        for field in priority_fields:
            if field in product_data and product_data[field]:
                value = str(product_data[field]).strip()
                if value and value != 'nan' and len(value) > 2:
                    info_lines.append(f"- {field}: {value}")
        
        # Ajouter autres champs pertinents (filtrer prix/stocks)
        for key, value in product_data.items():
            # Skip si déjà ajouté, exclu, ou contient des mots interdits
            if (key in priority_fields or 
                any(excl.lower() in key.lower() for excl in excluded_fields)):
                continue
                
            if value:
                value_str = str(value).strip()
                if value_str and value_str != 'nan' and len(value_str) > 2 and len(value_str) < 200:
                    info_lines.append(f"- {key}: {value_str}")
        
        return "\n".join(info_lines[:10]) if info_lines else "Produit moto de qualité"
    
    def generate_description(
        self,
        product_data: Dict,
        language: str = "fr",
        category: Optional[str] = None,
        temperature: float = 0.7,
        custom_instructions: Optional[str] = None,
        force_regenerate: bool = False
    ) -> Optional[str]:
        """
        Génère une description SEO pour un produit
        
        Args:
            product_data: Données du produit (dict avec clés: reference, designation, marque, etc.)
            language: Langue de la description (fr, en, it, es, de, nl, pt)
            category: Catégorie produit (casque, blouson, etc.) - auto-détecté si None
            temperature: Créativité de la génération (0-1)
            custom_instructions: Instructions additionnelles optionnelles
            force_regenerate: Forcer régénération même si en cache
            
        Returns:
            Description générée ou None si erreur
        """
        if not self.is_available():
            logger.error("Ollama non disponible")
            return None
        
        # Vérifier cache si activé et pas de force
        if self.cache and not force_regenerate:
            cached = self.cache.get(product_data, language)
            if cached:
                return cached['description']
        
        # Détecte la catégorie si non fournie
        if not category:
            category = self._detect_product_category(product_data)
        
        # Extrait les infos produit
        product_info = self._extract_product_info(product_data)
        
        # 🌐 ENRICHISSEMENT WEB (recherche Google via Serper API)
        web_context = ""
        if self.use_web_search and self.web_searcher:
            # Retry sur la recherche web
            for attempt in range(3):
                try:
                    # Recherche sur Google avec MARQUE + RÉFÉRENCE
                    search_result = self.web_searcher.search_product_info(product_data)
                    
                    if search_result.get('found'):
                        # Formater le contexte pour l'IA
                        raw_context = search_result.get('context', '')
                        if raw_context:
                            # Ajouter des instructions pour l'IA
                            web_context = f"""

🌐 INFORMATIONS TROUVÉES SUR LE WEB (à utiliser pour enrichir):
{raw_context}

⚠️ ATTENTION: 
- Utilise UNIQUEMENT les infos techniques (matériaux, construction, caractéristiques)
- NE MENTIONNE PAS les modèles de moto compatibles trouvés sur le web
- Les modèles compatibles sont UNIQUEMENT ceux présents dans les données du catalogue ci-dessus
- Enrichis la description avec les aspects techniques et la réputation de la marque
"""
                            logger.info(f"✅ Contexte web enrichi pour {product_data.get('Référence', 'produit')}")
                    else:
                        # Fallback: contexte intelligent basé sur la marque
                        web_context = self._create_enhanced_context(product_data, category)
                        if web_context:
                            logger.info(f"💡 Contexte expert (fallback) pour {product_data.get('Référence', 'produit')}")
                    break # Succès, on sort de la boucle
                except Exception as e:
                    logger.warning(f"⚠️ Erreur recherche web (tentative {attempt+1}/3): {e}")
                    time.sleep(1)
        
        # Récupère les suggestions de produits liés
        related_products = self._get_related_products(category)
        
        # Sélectionne le template (personnalisé > défaut)
        template_data = self.template_manager.get_template(category)
        template = template_data['structure']
        
        # Construit le prompt avec style Motoblouz + produits liés + contexte enrichi
        prompt = f"""Rédige une description produit pour ce {category} moto, style Motoblouz.

PRODUIT:
{product_info}
{web_context}

STRUCTURE CATALOGUE (100-130 mots):
1. PRÉSENTATION (1-2 phrases) : [Marque] propose ce [produit] pour [modèle/usage]
2. FABRICATION (2-3 phrases) : Matériaux, construction, finitions, qualité
3. CARACTÉRISTIQUES (liste à puces) : Spécifications techniques clés
4. COMPATIBILITÉ (1 phrase) : Modèles compatibles (UNIQUEMENT si dans le catalogue)
5. SUGGESTIONS (optionnel) : Produits complémentaires de façon discrète

📝 FORMATAGE MARKDOWN OBLIGATOIRE:
- Mets en **gras** les mots-clés importants : matériaux, marques, caractéristiques principales
- Utilise des listes à puces (•) pour les caractéristiques techniques
- Structure claire et lisible
- Pour les homologations importantes, utilise <b>texte</b> pour un gras HTML

EXEMPLE DE FORMATAGE:
"Arrow vous propose ce silencieux **Paris-Dakar** pour votre **Yamaha XT 600E**. 
Fabriqué en **acier inoxydable**, il offre une construction robuste.

**Caractéristiques principales** :
• Matériau : acier inoxydable
• Design ligne Paris-Dakar
• Construction robuste
• Finition professionnelle

<b>Ce silencieux n'est pas homologué pour un usage routier.</b>"

EXEMPLES DE FORMULATIONS PROFESSIONNELLES:
- "[Marque] vous propose ce [produit] pour votre [modèle]"
- "Fabriqué en [matériau], ce produit offre [caractéristique technique]"
- "Compatible avec les modèles [liste si disponible dans le catalogue]"
- "Construction [description technique] garantissant [bénéfice factuel]"
- "Disponible en [finitions/couleurs]. Montage [type de montage]"
- "Ce produit [est/n'est pas] homologué pour un usage routier"

RÈGLES D'UTILISATION DU CONTEXTE WEB:
- Utilise les infos techniques trouvées (matériaux, construction, certifications)
- Enrichis avec la réputation de la marque mentionnée
- NE PARLE PAS des modèles compatibles trouvés sur le web
- Les compatibilités sont UNIQUEMENT dans les données catalogue ci-dessus
- Reste naturel, ne mentionne pas que tu utilises des sources web

Longueur : {template_data.get('word_count', '100-120')} mots

Description:"""
        
        # Adapte à la langue
        if language != "fr":
            language_instructions = {
                "en": "Write in English, for English-speaking bikers.",
                "it": "Scrivi in italiano, per motociclisti italiani.",
                "es": "Escribe en español, para motociclistas españoles.",
                "de": "Schreibe auf Deutsch, für deutsche Motorradfahrer.",
                "nl": "Schrijf in het Nederlands, voor Nederlandse motorrijders.",
                "pt": "Escreva em português, para motociclistas portugueses."
            }
            
            if language in language_instructions:
                prompt = language_instructions[language] + "\n\n" + prompt
        
        # Ajoute instructions personnalisées
        if custom_instructions:
            prompt += f"\n\nInstructions supplémentaires: {custom_instructions}"
        
        # Système prompt pour descriptions techniques pures
        system_prompt = """Tu es un rédacteur professionnel de catalogue moto pour Motoblouz.

TON ET STYLE:
- Style catalogue professionnel : factuel, descriptif, technique
- Ton expert mais accessible, jamais marketing ou émotionnel
- Présentation structurée des informations produit
- Vocabulaire technique précis (matériaux, normes, spécifications)
- Focus sur les caractéristiques réelles et vérifiables
- UTILISE le formatage Markdown : **gras** pour mots-clés et • listes à puces pour caractéristiques
- UTILISE <b>texte</b> pour mettre en gras les informations d'homologation importantes

STRUCTURE CATALOGUE (100-130 mots):
1. PRÉSENTATION (1-2 phrases) : [Marque] propose ce [produit] pour [modèle/usage]
2. FABRICATION (2-3 phrases) : Matériaux, construction, finitions, qualité
3. CARACTÉRISTIQUES (2-3 phrases) : Spécifications techniques, homologations, normes
4. COMPATIBILITÉ (1-2 phrases) : Modèles compatibles (UNIQUEMENT si dans le catalogue)
5. SUGGESTIONS (1 phrase optionnelle) : Produits complémentaires de façon discrète

VOCABULAIRE PROFESSIONNEL:
✅ Utilise : "propose", "conçu pour", "fabriqué en", "compatible avec", "disponible en", "homologué", "certifié"
✅ Parle de : matériaux, construction, spécifications, normes, finitions, montage, entretien
✅ Suggestions (discret) : "À associer avec", "Disponible également"
❌ Évite absolument : "top", "incroyable", "bête de course", "faire tourner les têtes", "booster", "frissonner", "dominer"

IMPÉRATIF:
- AUCUN prix, tarif, montant, euro
- Langue: {language} uniquement
- Style CATALOGUE PROFESSIONNEL : factuel, technique, descriptif
- AUCUN marketing émotionnel (pas de "incroyable", "vous allez adorer", "sensation")
- Focus sur caractéristiques techniques vérifiables
- Suggère produits liés de façon discrète si pertinent
- NE MENTIONNE PAS les modèles de moto compatibles sauf s'ils sont dans les données catalogue
- Utilise le contexte web uniquement pour les aspects techniques et la réputation de la marque""".format(language=language)
        
        # Génération avec Retry
        description = None
        for attempt in range(3):
            try:
                logger.info(f"🎨 Génération description {category} en {language} (tentative {attempt+1}/3)...")
                
                description = self.ollama.generate(
                    prompt=prompt,
                    system=system_prompt,
                    temperature=temperature,
                    max_tokens=300  # Optimisé : réduit de 400 à 300 (-25% temps)
                )
                
                if description:
                    break # Succès
            except Exception as e:
                logger.warning(f"⚠️ Erreur génération (tentative {attempt+1}/3): {e}")
                time.sleep(1)
        
        if description:
            # Nettoie la description
            description = description.strip()
            
            # Validation longueur (150-200 mots optimal)
            word_count = len(description.split())
            if word_count < 100:
                logger.warning(f"⚠️  Description courte: {word_count} mots (optimal: 150-200)")
            elif word_count > 250:
                logger.warning(f"⚠️  Description longue: {word_count} mots (optimal: 150-200)")
            else:
                logger.info(f"✅ Description générée ({len(description)} caractères, {word_count} mots)")
        else:
            logger.error("❌ Échec génération description après 3 tentatives")
        
        return description
    
    def generate_full_seo(
        self,
        product_data: Dict,
        language: str = "fr",
        force_regenerate: bool = False
    ) -> Dict:
        """
        Génère description + titre + meta pour un produit (avec cache)
        Utilise le mode JSON d'OpenAI si disponible pour une génération unique et rapide.
        """
        # Vérifier cache d'abord
        if self.cache and not force_regenerate:
            cached = self.cache.get(product_data, language)
            if cached:
                return cached
        
        # Optimisation OpenAI: Génération unique en JSON
        if self.provider == "openai" and hasattr(self.client, 'generate_with_json'):
            try:
                # Préparation du contexte (similaire à generate_description)
                category = self._detect_product_category(product_data)
                product_info = self._extract_product_info(product_data)
                
                # Web Search (simplifié pour ce mode)
                web_context = ""
                if self.use_web_search and self.web_searcher:
                    try:
                        search_result = self.web_searcher.search_product_info(product_data)
                        if search_result.get('found'):
                            web_context = f"\nCONTEXTE WEB:\n{search_result.get('context', '')}\n"
                    except:
                        pass
                
                if not web_context:
                    web_context = self._create_enhanced_context(product_data, category)

                # Prompt unifié JSON
                system_prompt = "Tu es un expert SEO e-commerce. Tu dois générer une fiche produit complète au format JSON strict."
                
                prompt = f"""Génère le contenu SEO pour ce produit moto ({category}).

DONNÉES PRODUIT:
{product_info}
{web_context}

INSTRUCTIONS:
1. Description: Style Motoblouz, factuel, technique, formatage Markdown (**gras**, • puces). 120-150 mots.
2. Titre SEO: Accrocheur, < 60 caractères, inclut Marque + Produit.
3. Meta Description: Incitative, < 160 caractères.

FORMAT DE RÉPONSE ATTENDU (JSON):
{{
    "description": "Texte de la description avec formatage Markdown...",
    "seo_title": "Titre optimisé...",
    "meta_description": "Meta description..."
}}

Langue: {language}
"""
                # Appel API en mode JSON
                result_json = self.client.generate_with_json(
                    prompt=prompt,
                    system=system_prompt,
                    temperature=0.7,
                    max_tokens=1000
                )
                
                if result_json and 'description' in result_json:
                    # Sauvegarder dans le cache
                    if self.cache:
                        self.cache.set(
                            product_data,
                            result_json.get('description', ''),
                            result_json.get('seo_title', ''),
                            result_json.get('meta_description', ''),
                            language
                        )
                    return result_json
                    
            except Exception as e:
                logger.warning(f"⚠️ Échec génération JSON ({e}), fallback sur méthode séquentielle")

        # Fallback: Génération séquentielle (Ollama ou échec JSON)
        description = self.generate_description(product_data, language, force_regenerate=force_regenerate)
        seo_title = self.generate_seo_title(product_data)
        meta_description = self.generate_meta_description(product_data)
        
        result = {
            'description': description if description else "",
            'seo_title': seo_title if seo_title else "",
            'meta_description': meta_description if meta_description else ""
        }
        
        # Sauvegarder dans le cache
        if self.cache and description and seo_title and meta_description:
            self.cache.set(
                product_data,
                description,
                seo_title,
                meta_description,
                language
            )
        
        return result
    
    def generate_batch(
        self,
        products: List[Dict],
        language: str = "fr",
        progress_callback=None,
        max_workers: int = 1  # Par défaut 1 pour économiser RAM
    ) -> List[Dict]:
        """
        Génère des descriptions pour plusieurs produits EN PARALLÈLE
        
        Args:
            products: Liste de dictionnaires produits
            language: Langue de génération
            progress_callback: Fonction appelée avec (current, total) pour suivre la progression
            max_workers: Nombre de générations simultanées (1 recommandé pour économiser RAM)
            
        Returns:
            Liste de dicts avec 'description', 'seo_title', 'meta_description'
        """
        results = []
        total = len(products)
        
        logger.info(f"🎨 Génération de {total} descriptions en {language} (parallèle x{max_workers})...")
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Soumettre toutes les tâches
            future_to_product = {
                executor.submit(self.generate_full_seo, product, language): product
                for product in products
            }
            
            # Récupérer les résultats au fur et à mesure
            completed = 0
            for future in as_completed(future_to_product):
                completed += 1
                if progress_callback:
                    progress_callback(completed, total)
                
                try:
                    result = future.result()
                    results.append(result)
                    
                    # Libérer la RAM toutes les 10 générations pour économiser RAM
                    if max_workers == 1 and completed % 10 == 0:
                        logger.info(f"🧹 Libération RAM après {completed} générations...")
                        self.ollama.unload_model()
                        import gc
                        gc.collect()  # Force garbage collection Python
                        
                except Exception as e:
                    logger.error(f"❌ Erreur génération: {e}")
                    results.append({
                        'description': "",
                        'seo_title': "",
                        'meta_description': ""
                    })
        
        elapsed = time.time() - start_time
        avg_time = elapsed / total if total > 0 else 0
        logger.info(f"✅ {total} descriptions générées en {elapsed:.1f}s (moyenne: {avg_time:.1f}s/produit)")
        
        return results
    
    def generate_batch_sequential(
        self,
        products: List[Dict],
        language: str = "fr",
        progress_callback=None
    ) -> List[Dict]:
        """
        Génère des descriptions pour plusieurs produits SÉQUENTIELLEMENT (legacy)
        
        Args:
            products: Liste de dictionnaires produits
            language: Langue de génération
            progress_callback: Fonction appelée avec (current, total) pour suivre la progression
            
        Returns:
            Liste de dicts avec 'description', 'seo_title', 'meta_description'
        """
        results = []
        total = len(products)
        
        logger.info(f"🎨 Génération de {total} descriptions en {language} (séquentiel)...")
        
        for i, product in enumerate(products, 1):
            if progress_callback:
                progress_callback(i, total)
            
            result = self.generate_full_seo(product, language)
            results.append(result)
            
            logger.info(f"  [{i}/{total}] {'✅' if result.get('description') else '❌'}")
        
        success_count = sum(1 for r in results if r.get('description'))
        logger.info(f"✅ {success_count}/{total} descriptions générées avec succès")
        
        return results
    
    def generate_seo_title(self, product_data: Dict, max_length: int = 60) -> Optional[str]:
        """
        Génère un titre SEO optimisé
        
        Args:
            product_data: Données produit
            max_length: Longueur max du titre (pour balise <title>)
            
        Returns:
            Titre SEO ou None
        """
        if not self.is_available():
            return None
        
        product_info = self._extract_product_info(product_data)
        
        prompt = f"""Crée un titre SEO optimisé pour ce produit moto (max {max_length} caractères).

{product_info}

Le titre doit:
- Contenir la marque, le type de produit et 1-2 mots-clés
- Être accrocheur et précis
- Respecter {max_length} caractères maximum
- Être optimisé pour le référencement Google

Réponds UNIQUEMENT avec le titre, sans guillemets ni explication."""
        
        title = self.ollama.generate(
            prompt=prompt,
            system="Tu es un expert SEO spécialisé en e-commerce moto.",
            temperature=0.5,
            max_tokens=50  # Optimisé pour titres courts
        )
        
        if title:
            title = title.strip().strip('"').strip("'")
            if len(title) > max_length:
                title = title[:max_length-3] + "..."
        
        return title
    
    def generate_meta_description(self, product_data: Dict, max_length: int = 160) -> Optional[str]:
        """
        Génère une meta description SEO
        
        Args:
            product_data: Données produit
            max_length: Longueur max (pour balise meta description)
            
        Returns:
            Meta description ou None
        """
        if not self.is_available():
            return None
        
        product_info = self._extract_product_info(product_data)
        
        prompt = f"""Crée une meta description SEO pour ce produit moto (max {max_length} caractères).

{product_info}

La meta description doit:
- Résumer les atouts principaux du produit
- Inciter au clic
- Contenir 2-3 mots-clés pertinents
- Respecter {max_length} caractères maximum

Réponds UNIQUEMENT avec la meta description, sans guillemets."""
        
        meta = self.ollama.generate(
            prompt=prompt,
            system="Tu es un expert SEO spécialisé en e-commerce.",
            temperature=0.5,
            max_tokens=80  # Optimisé pour meta descriptions
        )
        
        if meta:
            meta = meta.strip().strip('"').strip("'")
            if len(meta) > max_length:
                meta = meta[:max_length-3] + "..."
        
        return meta


def test_generator():
    """Teste le générateur de descriptions"""
    print("\n" + "="*80)
    print("🧪 TEST GÉNÉRATEUR DE DESCRIPTIONS PRODUITS")
    print("="*80)
    
    generator = ProductDescriptionGenerator()
    
    if not generator.is_available():
        print("\n❌ Ollama non disponible - impossible de tester")
        return False
    
    print("\n✅ Générateur initialisé")
    
    # Produit de test
    test_product = {
        'reference': 'CASQUE-001',
        'designation': 'Casque intégral sport',
        'marque': 'AGV',
        'modele': 'K6',
        'categorie': 'Casques',
        'couleur': 'Noir mat',
        'taille': 'L',
        'materiau': 'Fibre de carbone',
        'homologation': 'ECE 22.06',
        'poids': '1350g',
        'caracteristiques': 'Ventilation optimisée, écran anti-buée, spoiler arrière'
    }
    
    print("\n🔹 Test 1: Description française...")
    desc_fr = generator.generate_description(test_product, language="fr")
    
    if desc_fr:
        print(f"✅ Description générée ({len(desc_fr)} caractères):")
        print("-" * 80)
        print(desc_fr[:300] + "..." if len(desc_fr) > 300 else desc_fr)
        print("-" * 80)
    else:
        print("❌ Échec génération")
        return False
    
    print("\n🔹 Test 2: Titre SEO...")
    title = generator.generate_seo_title(test_product)
    
    if title:
        print(f"✅ Titre: {title}")
    
    print("\n🔹 Test 3: Meta description...")
    meta = generator.generate_meta_description(test_product)
    
    if meta:
        print(f"✅ Meta: {meta}")
    
    print("\n" + "="*80)
    print("✅ TESTS GÉNÉRATEUR RÉUSSIS")
    print("="*80)
    return True


if __name__ == "__main__":
    test_generator()
