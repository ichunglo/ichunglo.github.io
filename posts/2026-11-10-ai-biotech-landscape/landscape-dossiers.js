// Evidence-limited audit of all companies in the current universe, 2026-11-11.
// No statement that an asset or controlling shareholder is absent follows from nondisclosure.
(() => {
  const mk = (portfolio, rights, url) => ({portfolio,rights,url});
  const dossiers = {
    'Recursion':mk('Wholly owned: REC-4881, REC-1245, REC-4539, REC-7735, and preclinical REC-102. The company also lists partnered programs.','Sanofi optioned a collaboration candidate; Roche/Genentech advanced a neuroscience target. Asset-specific rights differ.','https://www.recursion.com/pipeline'),
    'Generate:Biomedicines':mk('GB-0895: severe asthma and COPD; GB-4362: use with MMAE antibody-drug conjugates; GB-5267: ovarian cancer CAR-T. Additional programs are undisclosed.','Company pipeline identifies Roswell Park on GB-5267 and confidential platform collaborations; full program-by-program rights are not stated on the pipeline page.','https://generatebiomedicines.com/pipeline/'),
    'Absci':mk('ABS-201 in androgenetic alopecia and endometriosis; ABS-202 in immunology/inflammation. The company pipeline also lists unnamed partnerships.','Internal assets and collaboration programs are reported; detailed asset-by-asset commercial rights are not established by the linked pipeline.','https://www.absci.com/our-pipeline/'),
    'Iambic Therapeutics':mk('IAM1363 (HER2); IAM217 (KIF18A); IAM-C1 (CDK2/4), plus undisclosed partnered programs. IAM1363 is clinical; do not infer phase from the other bars.','Company separates owned and partnered programs; individual contract rights vary and some partners or targets remain undisclosed.','https://www.iambic.ai/pipeline'),
    'Secarna Pharmaceuticals':mk('SECN-15 is an NRP1 antisense program in IND-enabling work. Company describes additional proprietary and partnered programs.','SECN-15 is described as proprietary; ownership and stage of other programs are not individually disclosed in the source.','https://www.secarna.com/pipeline'),
    'Cradle':mk('Protein-engineering software and customer projects; no owned clinical asset was identified in reviewed platform and collaboration sources.','Bayer and UCB have licensed or adopted the platform. No transfer of underlying customer therapeutic ownership is inferred.','https://www.cradle.bio/blog/ucb'),
    'Owkin':mk('Drug pipeline includes OKN4395; company also lists diagnostic applications, which are not therapeutic assets.','Epkin, an Owkin affiliate, sponsors the OKN4395 study. Owkin licenses its K Pro platform to partners including Sanofi.','https://www.owkin.com/pipeline/pipeline'),
    'insitro':mk('CTRO-1013 targets a liver-fat and fibrosis program; the company describes additional discovery programs. Clinical entry must be verified separately.','The company reports internal programs and collaborations, including Bristol Myers Squibb and Lilly. Rights for each program require its own agreement.','https://www.insitro.com/news/insitro-presents-new-data-demonstrating-its-ai-discovered-mash-candidate-shows-anti-fibrotic-signal-beyond-liver-fat-reduction-at-the-american-diabetes-association-86th-scientific-sessions/'),
    'Enveda':mk('ENV-294: atopic dermatitis and asthma; ENV-308: post-weight-loss maintenance; ENV-6946: inflammatory bowel disease. The company reports additional undisclosed candidates.','Company describes these as its drug pipeline; exact third-party rights and current stage of every preclinical candidate are not fully disclosed.','https://enveda.com/pipeline/'),
    'Nabla Bio':mk('Antibody platform and partnership work; no named owned clinical asset was established in reviewed sources.','The company identifies AstraZeneca, Bristol Myers Squibb and Takeda as collaborators; target-specific rights are not stated in that source.','https://www.nabla.bio/careers/ml-engineer'),
    'Isomorphic Labs':mk('The company describes its own discovery programs and pharma-partnered research; specific named clinical candidates are not established in these sources.','Novartis and Eli Lilly collaborations are disclosed. Alphabet and other investors participated in funding; a current controlling stake is not established here.','https://www.isomorphiclabs.com/partnerships'),
    'Biorelate':mk('Galactic AI knowledge curation and target-selection software; no owned therapeutic pipeline was established in reviewed sources.','Commercial platform use does not establish ownership of customers’ therapeutic programs.','https://biorelate.com/company'),
    'Formation Bio':mk('BLKR201 is an in-licensed clinical program. The company reports other acquired or licensed assets; a complete current asset list was not established.','BLKR201 was licensed from Lynk; Sanofi and OpenAI collaborated on a recruitment tool. Software collaboration and drug rights are separate.','https://www.formation.bio/press/formation-bio-doses-first-participant-in-phase-1-trial-of-blkr201-a-cns-penetrant-tyk2-inhibitor'),
    'Schrödinger':mk('Internal SGR-1505 and SGR-3515, plus collaborative programs, are described on the therapeutic pipeline.','The company supplies software and runs internal and partnered discovery. Bristol Myers Squibb and Simcere are listed; individual programs have distinct rights.','https://www.schrodinger.com/pipeline/'),
    'Latent Labs':mk('Latent-X protein-binder design platform; no owned clinical drug pipeline was established in the reviewed platform source.','The platform describes commercial use under a license; customer rights are governed by applicable terms.','https://www.latentlabs.com/latent-x/'),
    'Iktos':mk('Makya generative design, Spaya retrosynthesis, and partnered discovery services; no named owned clinical asset established here.','The company offers software and discovery collaborations. Astellas is a disclosed platform customer; individual therapeutic rights are contract-specific.','https://iktos.ai/resources/news/iktos-announces-agreement-with-astellas-for-use-of-its-synthesis-aware-generative-ai-platform'),
    'PostEra':mk('Wholly owned PERA-5720 and another PMOS program; PERA-8103 and a female infertility program were acquired by Merck KGaA; additional partnered programs are listed.','Company explicitly distinguishes wholly owned programs, acquired fertility programs, and partnered milestones/royalties. Current stages need program-level verification.','https://postera.ai/drug-discovery/'),
    'Unlearn':mk('Digital-twin and trial-analysis services; no owned therapeutic pipeline was identified in reviewed sources.','Models and scientific services are provided to trial sponsors. A model-assisted trial does not imply ownership of its therapeutic asset.','https://www.unlearn.ai/solutions/clinical-trial-assessment'),
    'WhiteLab Genomics':mk('ALFRED delivery-vehicle and payload design, including partner research; no named owned clinical asset established in reviewed sources.','The company names Sanofi and Cytiva among partners; program-specific intellectual-property terms are not disclosed in the cited press kit.','https://whitelabgx.com/press-kit'),
    'Tempus AI':mk('Diagnostic products and life-science data services; no company-owned therapeutic pipeline was established from reviewed sources.','The company licenses data and software to biopharma and provides diagnostics; those business activities do not confer ownership of a customer’s drugs.','https://www.tempus.com/solutions/real-world-data/'),
    'Inductive Bio':mk('ADMET and PK prediction software; no named owned therapeutic pipeline established in reviewed sources.','The company describes partner access to models; program and data rights depend on the specific agreement.','https://www.inductive.bio/news/models-are-now-available-in-claude-chatgpt-and-benchling'),
    'Immunai':mk('AMICA single-cell immune data and drug-discovery collaborations; no owned clinical therapeutic was established in reviewed sources.','The cited source describes clinical and industry collaborations; rights to each resulting candidate are not disclosed there.','https://www.immunai.com/platform/'),
    'Eclipsebio':mk('RNA design, off-target testing and characterization services; no owned clinical therapeutic identified in reviewed sources.','Company provides services and partnerships; client program ownership cannot be inferred from the service relationship.','https://eclipsebio.com/'),
    'Relation Therapeutics':mk('Internal osteoporosis and chronic kidney disease programs; partnered skin fibrosis, atopic disease, osteoarthritis and Project Morgan programs.','The pipeline identifies GSK on skin fibrosis, osteoarthritis and Project Morgan, and Novartis on atopic disease; the internal osteoporosis program is labeled internal.','https://www.relationrx.com/pipeline'),
    'Causaly':mk('AI evidence-search and target-prioritization software; no owned clinical therapeutic was established in reviewed sources.','The platform supports research organizations; rights to a customer’s drug programs are not inferred.','https://www.causaly.com/use-cases/target-identification-prioritization'),
    'BigHat Biosciences':mk('BHB810 is clinical; BHB299, BHB-AV, BHB-VH and unnamed partner programs are listed. The visual pipeline does not establish every program’s precise stage in text.','Company describes a mix of wholly owned and partnered programs. Rights of each unlabelled program require additional disclosure.','https://www.bighatbio.com/therapeutics'),
    'Chai Discovery':mk('Chai-2 antibody and binder design platform; no owned clinical therapeutic was established in reviewed sources.','The company reports collaborations with Novartis, GSK and Roche; drug-specific ownership terms are not established here.','https://www.chaidiscovery.com/news'),
    'AQEMIA':mk('Company reports wholly owned and partnered discovery programs; its most advanced preclinical programs are in vivo optimization. Named clinical assets were not established.','Sanofi collaboration expanded in 2026; program-specific ownership and development rights require the relevant agreements.','https://aqemia.com/pipeline/'),
    'Atomic AI':mk('RNA-targeted small molecules and RNA therapeutics are described; named clinical programs and their current stage were not established in reviewed sources.','Company seeks partnerships. No statement is made about control of an undisclosed program.','https://atomic.ai/partnering/'),
    'Dyno Therapeutics':mk('AI-guided AAV capsid design and partnered gene-delivery programs; no owned clinical asset established here.','Roche exercised a neurological capsid license in 2025 and Astellas exercised a skeletal-muscle capsid license in 2026; their licensed therapies are not Dyno-owned assets.','https://www.dynotx.com/partnerships'),
    'Outpace Bio':mk('OPB-201: PRAME TCR-T, early clinical; OPB-401: CD19/CD20 in-vivo CAR-T at candidate nomination; additional discovery and Lyell programs are listed.','The company separates internal programs from a confidential Lyell program; detailed rights for each collaboration were not established.','https://www.outpacebio.com/our-science'),
    'Profluent':mk('Protein-design and genome-editor platform; no named owned clinical therapeutic established in reviewed sources.','The company reports a collaboration with Ensoma on base editors; specific program ownership terms were not established.','https://www.profluent.bio/media'),
    'Relay Therapeutics':mk('Zovegalisib/RLY-2608 in breast cancer and vascular anomalies; RLY-8161 in NRAS-mutant solid tumors. Lirafugratinib has FDA approval.','Relay licensed lirafugratinib rights to Elevar, the FDA applicant. Zovegalisib remains investigational.','https://ir.relaytx.com/news-releases/news-release-details/relay-therapeutics-reports-third-quarter-2026-financial-results'),
    'Xaira Therapeutics':mk('The company describes XA-1 through XA-9 discovery programs across oncology, immunology/inflammation and undisclosed areas. Precise stage from visual bars requires direct verification.','Company describes internal research and pipeline; public program-by-program legal ownership and clinical status are not fully disclosed in the reviewed source.','https://www.xaira.com/platform'),
    'Terray Therapeutics':mk('Internal and partnered small-molecule discovery programs; no named clinical asset was established in the reviewed sources.','Bristol Myers Squibb collaboration reported a discovery milestone; milestone achievements do not establish program approval.','https://www.terraytx.ai/news-and-research/terray-therapeutics-achieves-ai-enabled-drug-discovery-milestone-in-collaboration-with-bristol-myers-squibb'),
    'Eikon Therapeutics':mk('EIK1001, EIK1003, EIK1004 and EIK1005 are described as clinical candidates; additional discovery programs are disclosed.','EIK1001, EIK1003 and EIK1004 were in-licensed. The company filing and individual contracts govern rights; AI discovery must not be assumed.','https://investors.eikontx.com/static-files/de8ba37f-ab20-4c78-9a50-e513657dc959'),
    'CHARM Therapeutics':mk('CHM-029 is the disclosed menin-inhibitor clinical program; other program-level details were not established in reviewed sources.','Company identifies CHM-029 as its candidate. Precise partnering and territory rights are not established in the cited announcement.','https://charmtx.com/charm-therapeutics-announces-first-patient-dosed-and-first-cohort-fully-enrolled-in-its-phase-i-ii-clinical-trial-of-chm-029-for-aml/'),
    'Superluminal Medicines':mk('Company pipeline includes an MC4R obesity program and additional GPCR discovery programs. The company sponsors the registered Phase 1 SUN-0864 study, which was not yet recruiting in the snapshot.','The company describes its pipeline; definitive territory and commercial rights for all programs were not established.','https://www.superluminalrx.com/pipeline/'),
    'Valo Health':mk('Company describes internal and partnered discovery programs. Historical registry records for OPL-0401 and OPL-0301 are linked; their registry statuses are unknown and withdrawn, respectively.','Novo Nordisk, Pfizer and Lundbeck collaborations are listed. Partnership rights are specific to each agreement; historical trial sponsorship does not establish current ownership.','https://www.valohealth.com/partnership'),
    'Pathos AI':mk('Pocenbrodib/FT-7051, DO-2, P-100/AZD4241 and JSKN016 are listed. Individual visual pipeline bars require study-level confirmation.','Alphamab developed JSKN016 and retains Greater China rights; Pathos licensed rights elsewhere. A Phase 3 study is sponsored by Alphamab.','https://www.pathos.com/pipeline'),
    'Intelligencia AI':mk('Clinical-trial probability and portfolio-analysis software; no owned therapeutic pipeline established in reviewed sources.','Predictive software does not establish ownership of the studies or drugs it models.','https://registry.elevategreece.gov.gr/company/intelligencia/'),
    'Healx':mk('HLX-1502 is in a Phase 2 neurofibromatosis type 1 study; company reports other rare-disease discovery work.','Healx is the HLX-1502 trial sponsor. Details of rights and other partnerships require program-specific disclosure.','https://clinicaltrials.gov/study/NCT06541847'),
    'Verge Labs (formerly Verge Genomics)':mk('VRG50635 completed healthy-volunteer testing; its ALS study was terminated and the company says it will not advance the program in ALS.','The company transitioned its strategy and name in 2026; do not present the discontinued ALS program as an active clinical asset.','https://www.vergelabs.blog/p/what-we-learned-from-the-trial-of'),
    'A-Alpha Bio':mk('Protein-interaction measurement, antibody design and molecular-glue discovery; no named owned clinical therapeutic established in reviewed sources.','The company describes internal and partnered research, including a Gilead collaboration; detailed candidate-level rights are not established.','https://www.aalphabio.com/applications/'),
    'Inceptive':mk('RNA foundation models and partnered RNAi research; no owned clinical program established in the reviewed collaboration announcement.','Alnylam collaboration targets RNAi drug design; the announcement does not establish a named clinical asset or full asset-specific rights.','https://investors.alnylam.com/press-release?id=12c82628-531a-443b-b21b-26cc5b51230b'),
    'Genesis Therapeutics':mk('Internal oncology and immunology discovery programs, including pan-mutant PIK3CA leads; no named clinical candidate established in the reviewed pipeline.','Gilead and Incyte collaborations are listed separately from the company’s wholly owned discovery pipeline.','https://www.genesis.ml/partners-pipeline'),
    'Alto Neuroscience':mk('Company pipeline lists ALTO-207, ALTO-300, ALTO-100, ALTO-101, ALTO-203, ALTO-202 and ALTO-208; stage varies by asset and study.','The pipeline presents company development programs; source documents do not establish all in-licensing or territorial terms.','https://altoneuroscience.com/pipeline/')
  };
  const listed = {
    'Recursion':['Public · Nasdaq: RXRX','https://www.sec.gov/Archives/edgar/data/1601830/000160183026000145/R1.htm'],
    'Generate:Biomedicines':['Public · Nasdaq: GENB','https://investors.generatebiomedicines.com/investor-faq/'],
    'Absci':['Public · Nasdaq: ABSI','https://investors.absci.com/news-releases/news-release-details/absci-report-business-updates-and-third-quarter-2026-financial'],
    'Iambic Therapeutics':['Public · Nasdaq: IAM','https://ir.iambic.ai/news-releases/news-release-details/iambic-announces-pricing-initial-public-offering'],
    'Schrödinger':['Public · Nasdaq: SDGR','https://ir.schrodinger.com/stock-info/stock-quote/default.aspx'],
    'Tempus AI':['Public · Nasdaq: TEM','https://investors.tempus.com/news/news-details/2026/Tempus-Reports-Third-Quarter-2026-Results/default.aspx'],
    'Eikon Therapeutics':['Public · Nasdaq: EIKN','https://investors.eikontx.com/news-releases/news-release-details/eikon-therapeutics-presents-data-parp1-selective-and-wrn'],
    'Relay Therapeutics':['Public · Nasdaq: RLAY','https://ir.relaytx.com/news-releases/news-release-details/relay-therapeutics-reports-third-quarter-2026-financial-results'],
    'Alto Neuroscience':['Public · NYSE: ANRO','https://investors.altoneuroscience.com/news/news-details/2026/Alto-Neuroscience-Announces-Participation-in-Upcoming-Investor-Conferences-0e994aa6c/default.aspx'],
    'Biorelate':['UK registry: private limited company','https://find-and-update.company-information.service.gov.uk/company/09087514'],
    'Relation Therapeutics':['UK registry: private limited company','https://find-and-update.company-information.service.gov.uk/company/12305953'],
    'Isomorphic Labs':['Alphabet-founded; Alphabet is a disclosed investor. Current control percentage not verified.','https://www.isomorphiclabs.com/articles/isomorphic-labs-announces-series-b-investment-round']
  };
  // Private status is source-labelled, not evidence of independence or cap-table control.
  const privateSources = {
    'Secarna Pharmaceuticals':'https://www.linkedin.com/company/secarna-pharmaceuticals/',
    'Cradle':'https://www.linkedin.com/company/cradlebio',
    'Owkin':'https://uk.linkedin.com/company/owkin',
    'insitro':'https://www.nasdaqprivatemarket.com/company/insitro/',
    'Enveda':'https://in.linkedin.com/company/envedabio',
    'Nabla Bio':'https://www.linkedin.com/company/nabla-bio',
    'Formation Bio':'https://www.linkedin.com/company/formationbio',
    'Latent Labs':'https://www.nasdaqprivatemarket.com/company/latent-labs/',
    'Iktos':'https://www.linkedin.com/company/iktos',
    'PostEra':'https://www.linkedin.com/company/postera-ai',
    'Unlearn':'https://www.linkedin.com/company/unlearn-ai',
    'WhiteLab Genomics':'https://www.linkedin.com/company/whitelabgenomics/',
    'Inductive Bio':'https://www.linkedin.com/company/inductive-bio',
    'Immunai':'https://www.linkedin.com/company/immunai',
    'Eclipsebio':'https://www.linkedin.com/company/eclipse-bioinnovations',
    'Causaly':'https://www.linkedin.com/company/causaly',
    'BigHat Biosciences':'https://www.linkedin.com/company/bighat-biosciences',
    'Chai Discovery':'https://www.linkedin.com/company/chaidiscovery/',
    'AQEMIA':'https://www.linkedin.com/company/aqemia',
    'Atomic AI':'https://www.linkedin.com/company/atomic-ai-rna/',
    'Dyno Therapeutics':'https://www.nasdaqprivatemarket.com/company/dyno-therapeutics/',
    'Outpace Bio':'https://www.linkedin.com/company/outpace-bio',
    'Profluent':'https://www.linkedin.com/company/profluent-bio',
    'Xaira Therapeutics':'https://www.linkedin.com/company/xaira-therapeutics',
    'Terray Therapeutics':'https://www.nasdaqprivatemarket.com/company/terray-therapeutics/',
    'CHARM Therapeutics':'https://www.linkedin.com/company/charm-therapeutics',
    'Superluminal Medicines':'https://www.linkedin.com/company/superluminalrx',
    'Valo Health':'https://www.nasdaqprivatemarket.com/company/valo-health/',
    'Pathos AI':'https://www.linkedin.com/company/pathos-ai',
    'Intelligencia AI':'https://www.linkedin.com/company/intelligencia-ai',
    'Healx':'https://www.linkedin.com/company/healx',
    'Verge Labs (formerly Verge Genomics)':'https://www.linkedin.com/company/verge-analytics',
    'A-Alpha Bio':'https://www.nasdaqprivatemarket.com/company/a-alpha-bio/',
    'Inceptive':'https://ca.linkedin.com/company/inceptivenucleics',
    'Genesis Therapeutics':'https://www.linkedin.com/company/genesis-molecular-ai'
  };
  const rightsSources = {
    'Recursion':'https://ir.recursion.com/news-releases/news-release-details/recursion-reports-second-quarter-financial-results-genentech',
    'Generate:Biomedicines':'https://investors.generatebiomedicines.com/wp-content/uploads/2026/04/Generate-Biomedicines-Non-Confidential-Overview_April-2026-1.pdf',
    'Owkin':'https://www.owkin.com/newsfeed/owkin-to-build-ai-agents-as-part-of-a-multi-year-k-pro-collaboration-with-sanofi',
    'insitro':'https://www.insitro.com/publications-press/',
    'Formation Bio':'https://www.formation.bio/press/introducing-muse',
    'Causaly':'https://www.causaly.com/use-cases/target-identification-prioritization',
    'AQEMIA':'https://aqemia.com/news',
    'Profluent':'https://www.profluent.bio/media',
    'Pathos AI':'https://www.pathos.com/pathos-ai-enters-global-licensing-agreement-with-alphamab-oncology-on-jskn016-a-first-in-class-trop2-her3-bispecific-adc',
    'Verge Labs (formerly Verge Genomics)':'https://www.vergelabs.blog/p/why-were-becoming-verge-labs'
  };
  for (const company of window.landscapeCompanies) {
    company.dossier = dossiers[company.name];
    if (!company.dossier) throw new Error(`Missing ownership and portfolio audit: ${company.name}`);
    company.dossier.rightsUrl = rightsSources[company.name] || company.dossier.url;
    company.corporate = listed[company.name] || (privateSources[company.name] ? ['Reported privately held; controlling owners and cap table not established.',privateSources[company.name]] : ['Listing and controlling ownership not established in the reviewed sources.',null]);
  }
  const byName = name => window.landscapeCompanies.find(c => c.name === name);
  Object.assign(byName('PostEra'),{model:'Hybrid',asset:'PERA-5720 · company-owned discovery program; PERA-8103 and a female fertility program acquired by Merck KGaA.',caveat:'The company also reports partnered discovery programs. Do not treat a licensed or acquired partner asset as an owned clinical product.'});
  Object.assign(byName('Outpace Bio'),{asset:'OPB-201 · PRAME TCR-T, early clinical; OPB-401 · CD19/CD20 in-vivo CAR-T, candidate nomination.',caveat:'OPB-201 is in a Phase 1 registry study; OPB-401 has not been established as clinical in the cited company pipeline.'});
  byName('Outpace Bio').sources.unshift(['OPB-201 trial NCT07664735','https://clinicaltrials.gov/study/NCT07664735']);
  Object.assign(byName('Secarna Pharmaceuticals'),{asset:'SECN-15 · proprietary NRP1-targeted antisense program · IND-enabling.',caveat:'The company reports IND-enabling work and an intended 2027 submission; submission timing is a plan, not clinical entry.'});
  Object.assign(byName('Superluminal Medicines'),{asset:'SUN-0864 · Phase 1 registry study not yet recruiting; company also describes an MC4R obesity program.',caveat:'Registry listing is not evidence that dosing has started. The specific relationship between SUN-0864 and the MC4R program requires confirmation.'});
  byName('Superluminal Medicines').sources.unshift(['SUN-0864 trial NCT07905560','https://clinicaltrials.gov/study/NCT07905560']);
  Object.assign(byName('Genesis Therapeutics'),{name:'Genesis Molecular AI (formerly Genesis Therapeutics)',asset:'Internal oncology and immunology discovery programs; partnered Gilead and Incyte research.',caveat:'The company’s current site uses Genesis Molecular AI; exact clinical candidates and full asset rights are not established by the reviewed pipeline.'});
  byName('Atomic AI').location = 'San Francisco, California';
})();
