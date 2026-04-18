export type CompanyInterpretation = {
  company_name: string;
  ticker?: string | null;
  primary_sector: string;
  subsector?: string | null;
  products_services: string[];
  technical_themes: string[];
  market_keywords: string[];
  research_need_summary: string;
  school_affinities: string[];
  confidence: string;
};

export type PaperSummary = {
  id: string;
  title: string;
  year?: number | null;
  venue?: string | null;
  citation_count: number;
  paper_url?: string | null;
  pdf_url?: string | null;
  ai_summary?: string | null;
};

export type CollaboratorSummary = {
  name: string;
  affiliation?: string | null;
  is_uofu: boolean;
  profile_url?: string | null;
  related_papers: string[];
};

export type StaffSummaryResponse = {
  staff_id: string;
  name: string;
  title?: string | null;
  primary_school?: string | null;
  school_affiliations: string[];
  department?: string | null;
  ai_research_summary: string;
  match_reason: string;
  score: number;
  recent_papers: PaperSummary[];
  most_cited_papers: PaperSummary[];
  key_outreach_points: string[];
  further_contacts: CollaboratorSummary[];
};

export type CompanyMatchResponse = {
  company: CompanyInterpretation;
  matches: StaffSummaryResponse[];
};

