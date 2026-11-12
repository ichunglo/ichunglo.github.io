// Asset-level research snapshot: public disclosures are time-bound and may not cover all programs.
window.assetAudit = [
['BigHat Biosciences','BHB810','Gastric and other gastrointestinal tumors','Phase 1; first patient dosed','BigHat describes BHB810 as its lead program; full territorial rights not established','2026-09-24','https://www.bighatbio.com/news/bighat-biosciences-announces-75-million-series-c-financing'],
['BigHat Biosciences','BHB299','CEACAM6-expressing solid tumors','Preclinical; company planned human testing in 2027','Company identifies it as its development candidate; detailed rights not established','2026-09-24','https://www.bighatbio.com/news/bighat-biosciences-announces-75-million-series-c-financing'],
['Evaxion','EVX-01','Advanced melanoma','Phase 2 study completed','Company clinical program; detailed territory rights not established','2026-11-04','https://clinicaltrials.gov/study/NCT05309421'],
['Evaxion','EVX-04','Acute myeloid leukemia','Preclinical; regulatory filing planned','Company program; detailed rights not established','2026-08-20','https://www.sec.gov/Archives/edgar/data/1828253/000117184326005672/exh_991.htm'],
['Evaxion','EVX-05','Glioblastoma','Discovery/preclinical','Company program; detailed rights not established','2026-08-17','https://www.sec.gov/Archives/edgar/data/1828253/000117184326005577/exh_991.htm'],
['Evaxion','EVX-03','Cancer vaccine','Discontinued in 2026','Historical program; current rights not established','2026-08-17','https://www.sec.gov/Archives/edgar/data/1828253/000117184326005577/exh_991.htm'],
['Evaxion','EVX-B2','Gonorrhea','Preclinical as of rights update','Company reported retaining global rights after MSD declined its option; subsequent changes not established','2025-12-19','https://www.sec.gov/Archives/edgar/data/1828253/000117184325008026/exh_991.htm'],
['Evaxion','EVX-B3','Infectious disease vaccine','Preclinical at license announcement','MSD exercised its option; milestones and royalties retained by Evaxion','2025-12-19','https://www.sec.gov/Archives/edgar/data/1828253/000117184325008026/exh_991.htm'],
['Cellarity SCD','CLY-124','Sickle cell disease','Phase 1','Separate Cellarity SCD company, not part of the Etcelera combination','2026-10-29','https://cellarity.com/news_item/an-update-on-our-sickle-cell-program/'],
['Pathos AI','JSKN016','Solid tumors','Phase 3 study sponsored by Alphamab','Pathos licensed rights outside Greater China; Alphamab retains Greater China rights','2026-11-11','https://www.pathos.com/pathos-ai-enters-global-licensing-agreement-with-alphamab-oncology-on-jskn016-a-first-in-class-trop2-her3-bispecific-adc'],
['Outpace Bio','OPB-101','Ovarian and related cancers','Study terminated','Outpace-sponsored study; current program rights not established by registry','2026-11-11','https://clinicaltrials.gov/study/NCT07030907'],
['Secarna Pharmaceuticals','SECN-15','NRP1 antisense program','IND-enabling','Described as a proprietary program; territorial rights not specified','2026-11-11','https://www.secarna.com/pipeline'],
['PostEra','PERA-5720','PMOS program','Company pipeline; exact stage to verify','Company describes as wholly owned','2026-11-11','https://postera.ai/drug-discovery/'],
['PostEra','PERA-8103','Fertility','Company pipeline; current stage to verify','Company reports Merck KGaA acquired program','2026-11-11','https://postera.ai/drug-discovery/'],
['Verge Labs (formerly Verge Genomics)','VRG50635','ALS','ALS study terminated; company stopped advancing in ALS','Company program; no claim about rights in other indications','2026-11-11','https://www.vergelabs.blog/p/what-we-learned-from-the-trial-of']
].map(([company,asset,indication,stage,rights,source_date,source])=>({company,asset,indication,stage,rights,source_date,source}));
// Additional named programs; stages are as displayed or described in the linked source.
window.assetAudit.push(...[
['Recursion','REC-4881','Familial adenomatous polyposis','Phase 2','Listed in the company’s wholly owned pipeline','https://www.recursion.com/pipeline'],
['Recursion','REC-1245','Solid tumors and lymphoma','Phase 1','Listed in the company’s wholly owned pipeline','https://www.recursion.com/pipeline'],
['Recursion','REC-4539','Solid tumors and hematologic cancers','Phase 1','Listed in the company’s wholly owned pipeline','https://www.recursion.com/pipeline'],
['Recursion','REC-7735','PIK3CA H1047R solid tumors','Phase 1','Listed in the company’s wholly owned pipeline','https://www.recursion.com/pipeline'],
['Recursion','REC-102','Hypophosphatasia','Preclinical; candidate profiling','Listed in the company’s wholly owned pipeline','https://www.recursion.com/pipeline'],
['Iambic Therapeutics','IAM1363','HER2-altered cancers','Phase 1/1b','Listed in the owned portion of the company pipeline','https://www.iambic.ai/pipeline'],
['Iambic Therapeutics','IAM217','Triple-negative breast cancer, ovarian cancer and other solid tumors','Preclinical; company describes advancing toward clinical development','Listed in the owned portion of the company pipeline','https://www.iambic.ai/pipeline'],
['Iambic Therapeutics','IAM-C1','HR-positive/HER2-negative breast cancer and CCNE1-amplified cancers','Company pipeline; precise stage requires confirmation','Listed in the owned portion of the company pipeline','https://www.iambic.ai/pipeline'],
['Absci','ABS-201','Androgenetic alopecia; endometriosis','Company reports Phase 1/2a and Phase 1 respectively','Internal program; detailed territorial rights not established','https://www.absci.com/our-pipeline/'],
['Absci','ABS-202','Immunology and inflammation','Candidate identification','Company pipeline program; detailed territorial rights not established','https://www.absci.com/our-pipeline/'],
['Pathos AI','Pocenbrodib / FT-7051','Prostate cancer; multiple myeloma','Phase 1 in prostate cancer; other indication phase to verify','Company development program; detailed territorial rights require agreement review','https://www.pathos.com/pipeline'],
['Pathos AI','DO-2','MET-altered non-small cell lung cancer','Company pipeline; specific stage requires verification','Company development program; detailed territorial rights require agreement review','https://www.pathos.com/pipeline'],
['Pathos AI','P-100 / AZD4241','ER-positive, HER2-negative breast cancer','Company pipeline; specific stage requires verification','Previously AZD4241; detailed territorial rights require agreement review','https://www.pathos.com/pipeline']
].map(([company,asset,indication,stage,rights,source])=>({company,asset,indication,stage,rights,source_date:'2026-11-11',source})));
window.assetAudit.push(...[
['Generate:Biomedicines','GB-0895','Severe asthma','Phase 3','Company pipeline; detailed rights require agreement review','https://generatebiomedicines.com/pipeline/'],
['Generate:Biomedicines','GB-0895','Chronic obstructive pulmonary disease','Phase 1','Company pipeline; detailed rights require agreement review','https://generatebiomedicines.com/pipeline/'],
['Generate:Biomedicines','GB-4362','Combined with MMAE antibody-drug conjugates','Phase 1','Company pipeline; detailed rights require agreement review','https://generatebiomedicines.com/pipeline/'],
['Generate:Biomedicines','GB-5267','Metastatic ovarian cancer','Phase 1','Roswell Park collaboration; allocation of rights not fully established','https://generatebiomedicines.com/pipeline/'],
['Enveda','ENV-294','Atopic dermatitis and asthma','Phase 2a reported by company; registry has additional phase detail','Company pipeline; detailed rights require agreement review','https://enveda.com/pipeline/'],
['Enveda','ENV-308','Post-weight-loss maintenance','Source conflicts: Phase 2 heading and Phase 1 text','Company pipeline; detailed rights require agreement review','https://enveda.com/pipeline/'],
['Enveda','ENV-6946','Inflammatory bowel disease','Phase 1 reported by company','Company pipeline; detailed rights require agreement review','https://enveda.com/pipeline/'],
['Alto Neuroscience','ALTO-207','Treatment-resistant depression','Company pipeline; precise current stage requires verification','Company program; complete territorial rights not established','https://altoneuroscience.com/pipeline/'],
['Alto Neuroscience','ALTO-300','Major depressive disorder','Company pipeline; see linked trial for study phase and status','Company program; complete territorial rights not established','https://altoneuroscience.com/pipeline/'],
['Alto Neuroscience','ALTO-100','Bipolar depression','Company pipeline; precise current stage requires verification','Company program; complete territorial rights not established','https://altoneuroscience.com/pipeline/'],
['Alto Neuroscience','ALTO-101','Cognitive impairment associated with schizophrenia','Company pipeline; precise current stage requires verification','Company program; complete territorial rights not established','https://altoneuroscience.com/pipeline/'],
['Alto Neuroscience','ALTO-203','Major depressive disorder','Company pipeline; see linked trial for study phase and status','Company program; complete territorial rights not established','https://altoneuroscience.com/pipeline/'],
['Alto Neuroscience','ALTO-202','Major depressive disorder','Company pipeline; precise current stage requires verification','Company program; complete territorial rights not established','https://altoneuroscience.com/pipeline/'],
['Alto Neuroscience','ALTO-208','Company pipeline; indication details require verification','Company pipeline; precise current stage requires verification','Company program; complete territorial rights not established','https://altoneuroscience.com/pipeline/']
].map(([company,asset,indication,stage,rights,source])=>({company,asset,indication,stage,rights,source_date:'2026-11-11',source})));
window.assetAudit.push(...[
['KMR301','Autoimmune disease','Preclinical','Formation lists the program; specific legal and territorial terms not established'],
['BLKR201','Inflammation','Phase 1','In-licensed from Lynk; detailed territorial terms not established'],
['Sprifermin','Knee osteoarthritis','Phase 2','Licensed from Merck KGaA; company identifies High Line Bio']
].map(([asset,indication,stage,rights])=>({company:'Formation Bio',asset,indication,stage,rights,source_date:'2026-11-12',source:'https://www.formation.bio/licensing-and-pipeline'})));
// Index additional explicitly named codes in company summaries; these entries require asset-specific review.
(() => {
const prefixes = ['REC','GB','ABS','IAM','SECN','OKN','CTRO','ENV','BLKR','SGR','PERA','BHB','OPB','RLY','EIK','CHM','SUN','OPL','HLX','VRG','ALTO','BEN','EVX','CLY'];
const pattern = new RegExp('\\b(?:' + prefixes.join('|') + ')[- ]?[A-Z]?[0-9]{1,5}\\b','g');
const key = s => s.toUpperCase().replace(/[^A-Z0-9]/g,'');
for (const c of window.landscapeCompanies) {
  for (const match of c.dossier.portfolio.matchAll(pattern)) {
    const code=match[0];
    if(window.assetAudit.some(a=>a.company===c.name && key(a.asset).includes(key(code)))) continue;
    window.assetAudit.push({company:c.name,asset:code,indication:'See company portfolio summary; asset-specific review pending',stage:'Asset-specific stage review pending',rights:'Asset-specific rights review pending',source_date:'2026-11-11',source:c.dossier.url});
  }
}
})();
// Xaira's reviewed portfolio describes the range XA-1 through XA-9; program-level details are undisclosed in that summary.
for(let n=1;n<=9;n++) window.assetAudit.push({company:'Xaira Therapeutics',asset:`XA-${n}`,indication:'Not individually specified in the reviewed company portfolio',stage:'Precise stage not established in the reviewed source',rights:'Company describes an internal pipeline; individual legal and territorial terms were not established',source_date:'2026-11-11',source:'https://www.xaira.com/platform'});
window.assetAudit.push(...[
['Relay Therapeutics','Lirafugratinib','Previously treated unresectable or metastatic FGFR2 fusion or rearrangement-positive intrahepatic cholangiocarcinoma','FDA approved in 2026','Relay licensed development rights to Elevar; FDA identifies Elevar as applicant','https://www.fda.gov/drugs/cancer-approvals/fda-approves-lirafugratinib-previously-treated-unresectable-locally-advanced-or-metastatic'],
['Schrödinger','SGR-6016','NLRP3 neurodegeneration program','Current stage not established from reviewed text','Company describes the program; specific ownership and territorial rights not established','https://www.schrodinger.com/pipeline/'],
['BigHat Biosciences','BHB-AV','Therapeutic program; indication not established from reviewed text','Current stage not established from reviewed text','Company lists the program; specific ownership and territorial rights not established','https://www.bighatbio.com/therapeutics'],
['BigHat Biosciences','BHB-VH','Therapeutic program; indication not established from reviewed text','Current stage not established from reviewed text','Company lists the program; specific ownership and territorial rights not established','https://www.bighatbio.com/therapeutics'],
['Evaxion','EVX-B1','Staphylococcus aureus','Listed in a 2026 company presentation; current stage not established','MSD associated with historical program; current rights not established','https://evaxion.ai/wp-content/uploads/2026/05/Evaxion-Q1-2026-Business-Update-Conference-Call.pdf']
].map(([company,asset,indication,stage,rights,source])=>({company,asset,indication,stage,rights,source_date:'2026-11-12',source})));
