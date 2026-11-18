CORPUS RAG RH — NOVALIA (ENTREPRISE ENTIÈREMENT FICTIVE)

Contenu :
- 13 PDF : 12 documents en vigueur et 1 ancienne politique de télétravail archivée.
- manifest_documents.csv : métadonnées recommandées pour l'indexation.
- Les contacts en domaine .example sont fictifs.
- Les règles sont inventées pour l'entraînement et ne constituent pas un conseil juridique ou une politique réelle.

Conseils d'indexation :
1. Extraire le texte PDF en conservant document_id, title, version, date, status et owner.
2. Ajouter ces champs dans les métadonnées de chaque chunk.
3. Pour une question sur la politique actuelle, filtrer status = "EN VIGUEUR".
4. Pour une question historique, autoriser explicitement les documents archivés.
5. Tester les questions qui nécessitent plusieurs documents, par exemple :
   - "Comment demander deux jours de télétravail et quels outils de sécurité utiliser ?"
   - "Quel est le délai de dépôt d'une note de frais et quelles sont les limites repas ?"
   - "Qui contacter en cas de perte d'ordinateur pendant un déplacement ?"
   - "Quelle est la règle actuelle de télétravail ? Compare-la avec l'ancienne."
6. Ne jamais considérer une réponse comme fiable si la source est archivée ou si la citation ne correspond pas au passage retrouvé.

Documents :
- RH-001.pdf — Guide d'accueil des collaborateurs [EN VIGUEUR]
- RH-002.pdf — Politique de congés et d'absences [EN VIGUEUR]
- RH-003.pdf — Politique de télétravail [EN VIGUEUR]
- RH-004.pdf — Politique de remboursement des frais professionnels [EN VIGUEUR]
- RH-005.pdf — Guide mutuelle et prévoyance [EN VIGUEUR]
- RH-006.pdf — Politique de parentalité et événements familiaux [EN VIGUEUR]
- RH-007.pdf — Procédure de recrutement et mobilité interne [EN VIGUEUR]
- RH-008.pdf — Politique de formation et développement des compétences [EN VIGUEUR]
- RH-009.pdf — Règlement intérieur — synthèse opérationnelle [EN VIGUEUR]
- IT-001.pdf — Politique de sécurité informatique et des accès [EN VIGUEUR]
- IT-002.pdf — Procédure de support informatique [EN VIGUEUR]
- FIN-001.pdf — Politique de déplacements professionnels [EN VIGUEUR]
- RH-003-ARCHIVE.pdf — Politique de télétravail — version archivée [ARCHIVÉE — NE PAS UTILISER]