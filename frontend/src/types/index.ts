// TypeScript interfaces matching backend Pydantic schemas

// --- Brief / Summary types for nested references ---

export interface CreatorBrief {
  creator_id: string;
  display_name: string;
  sort_name: string;
}

export interface CreatorRoleBrief {
  id: string;
  creator_id: string;
  role: string;
  notes?: string | null;
  creator?: CreatorBrief | null;
}

export interface WorkBrief {
  work_id: string;
  title: string;
  work_type: string;
  issue_number?: string | null;
}

export interface ArtifactBrief {
  artifact_id: string;
  title: string;
  format: string;
  publisher?: string | null;
}

export interface CollectionBrief {
  collection_id: string;
  name: string;
  collection_type: string;
}

export interface ArcBrief {
  arc_id: string;
  name: string;
  total_parts?: number | null;
  completion_status?: string | null;
}

export interface VolumeRunBrief {
  volume_run_id: string;
  name: string;
  publisher: string;
}

export interface CopyBrief {
  copy_id: string;
  copy_number: number;
  location?: string | null;
  condition?: string | null;
  borrower_name?: string | null;
  lent_date?: string | null;
}

export interface ArtifactWorkBrief {
  id: string;
  work_id: string;
  position: number;
  is_partial: boolean;
  collects_note?: string | null;
  work?: WorkBrief | null;
}

export interface ArtifactWorkWithArtifact {
  id: string;
  artifact_id: string;
  position: number;
  is_partial: boolean;
  collects_note?: string | null;
  artifact?: ArtifactBrief | null;
}

export interface WorkArcBrief {
  id: string;
  arc_id: string;
  arc_position?: number | null;
  arc?: ArcBrief | null;
}

export interface WorkCollectionBrief {
  id: string;
  collection_id: string;
  sequence_number?: number | null;
  collection?: CollectionBrief | null;
}

// --- Artifact types ---

export interface ArtifactCreate {
  title: string;
  format: string;
  publisher?: string | null;
  edition_year?: number | null;
  isbn_or_upc?: string | null;
  is_reprint?: boolean;
  original_publisher?: string | null;
  date_added?: string | null;
  owner?: string;
  is_pirated?: boolean;
  issue_number?: string | null;
  volume_run_id?: string | null;
  size?: string | null;
  main_genre?: string | null;
  sous_genre?: string | null;
  goodreads_url?: string | null;
  cover_image_path?: string | null;
  notes?: string | null;
}

export interface ArtifactUpdate {
  title?: string | null;
  format?: string | null;
  publisher?: string | null;
  edition_year?: number | null;
  isbn_or_upc?: string | null;
  is_reprint?: boolean | null;
  original_publisher?: string | null;
  date_added?: string | null;
  owner?: string | null;
  is_pirated?: boolean | null;
  issue_number?: string | null;
  volume_run_id?: string | null;
  size?: string | null;
  main_genre?: string | null;
  sous_genre?: string | null;
  goodreads_url?: string | null;
  cover_image_path?: string | null;
  notes?: string | null;
}

export interface ArtifactSummary {
  artifact_id: string;
  title: string;
  format: string;
  publisher?: string | null;
  owner?: string | null;
  issue_number?: string | null;
  cover_image_path?: string | null;
  volume_run?: VolumeRunBrief | null;
}

export interface PaginatedArtifacts {
  items: ArtifactSummary[];
  total: number;
}

export interface ArtifactDetail {
  artifact_id: string;
  title: string;
  format: string;
  publisher?: string | null;
  edition_year?: number | null;
  isbn_or_upc?: string | null;
  is_reprint: boolean;
  original_publisher?: string | null;
  date_added?: string | null;
  owner?: string | null;
  is_pirated: boolean;
  issue_number?: string | null;
  volume_run_id?: string | null;
  size?: string | null;
  main_genre?: string | null;
  sous_genre?: string | null;
  goodreads_url?: string | null;
  cover_image_path?: string | null;
  notes?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
  volume_run?: VolumeRunBrief | null;
  artifact_works: ArtifactWorkBrief[];
  copies: CopyBrief[];
  creators: CreatorRoleBrief[];
}

export interface CopyCreate {
  copy_number?: number;
  internal_sku?: string | null;
  location?: string | null;
  condition?: string | null;
  notes?: string | null;
}

export interface CopyDetail {
  copy_id: string;
  artifact_id: string;
  copy_number: number;
  internal_sku?: string | null;
  location?: string | null;
  condition?: string | null;
  borrower_name?: string | null;
  lent_date?: string | null;
  notes?: string | null;
}

// --- Work types ---

export interface WorkCreate {
  title: string;
  work_type: string;
  original_publication_year?: number | null;
  volume_run_id?: string | null;
  issue_number?: string | null;
  subject_tags?: string[] | null;
  is_narrative_nonfiction?: boolean | null;
  is_coffee_table_book?: boolean | null;
  goodreads_url?: string | null;
  comicvine_url?: string | null;
  notes?: string | null;
}

export interface WorkUpdate {
  title?: string | null;
  work_type?: string | null;
  original_publication_year?: number | null;
  volume_run_id?: string | null;
  issue_number?: string | null;
  subject_tags?: string[] | null;
  is_narrative_nonfiction?: boolean | null;
  is_coffee_table_book?: boolean | null;
  goodreads_url?: string | null;
  comicvine_url?: string | null;
  notes?: string | null;
}

export interface WorkSummary {
  work_id: string;
  title: string;
  work_type: string;
  original_publication_year?: number | null;
  issue_number?: string | null;
  volume_run?: VolumeRunBrief | null;
}

export interface WorkDetail {
  work_id: string;
  title: string;
  work_type: string;
  original_publication_year?: number | null;
  volume_run_id?: string | null;
  issue_number?: string | null;
  subject_tags?: string[] | null;
  is_narrative_nonfiction?: boolean | null;
  is_coffee_table_book?: boolean | null;
  goodreads_url?: string | null;
  comicvine_url?: string | null;
  notes?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
  volume_run?: VolumeRunBrief | null;
  artifact_works: ArtifactWorkWithArtifact[];
  arc_memberships: WorkArcBrief[];
  work_collections: WorkCollectionBrief[];
  creators: CreatorRoleBrief[];
}

// --- Collection types ---

export interface CollectionCreate {
  name: string;
  collection_type: string;
  parent_collection_id?: string | null;
  description?: string | null;
}

export interface CollectionSummary {
  collection_id: string;
  name: string;
  collection_type: string;
  parent_collection_id?: string | null;
  description?: string | null;
}

export interface WorkInCollection {
  work: WorkBrief;
  sequence_number?: number | null;
}

export interface CollectionDetail extends CollectionSummary {
  created_at?: string | null;
  updated_at?: string | null;
  works: WorkInCollection[];
  children: CollectionSummary[];
}

export interface CollectionTree extends CollectionSummary {
  children: CollectionTree[];
}

// --- Story Arc types ---

export interface ArcCreate {
  name: string;
  parent_arc_id?: string | null;
  total_parts?: number | null;
  completion_status?: string | null;
  description?: string | null;
}

export interface ArcSummary {
  arc_id: string;
  name: string;
  total_parts?: number | null;
  completion_status?: string | null;
  parent_arc_id?: string | null;
  description?: string | null;
}

export interface WorkInArc {
  work: WorkBrief;
  arc_position?: number | null;
  volume_run?: VolumeRunBrief | null;
}

export interface ArcDetail extends ArcSummary {
  created_at?: string | null;
  updated_at?: string | null;
  works: WorkInArc[];
  children: ArcBrief[];
}

export interface ArcTree extends ArcSummary {
  children: ArcTree[];
}

// --- Creator types ---

export interface CreatorCreate {
  first_name?: string | null;
  last_name?: string | null;
  display_name: string;
  sort_name: string;
  aliases?: string[] | null;
}

export interface CreatorSummary {
  creator_id: string;
  display_name: string;
  sort_name: string;
  first_name?: string | null;
  last_name?: string | null;
  aliases?: string[] | null;
}

export interface CreatorDetail extends CreatorSummary {
  roles: CreatorRoleBrief[];
  created_at?: string | null;
  updated_at?: string | null;
}

// --- Activity types ---

export interface ActivityCreate {
  user_profile: string;
  work_id: string;
  event_type: string;
  event_value?: string | null;
  timestamp: string;
}

export interface ActivityEntry {
  log_id: string;
  user_profile: string;
  work_id: string;
  event_type: string;
  event_value?: string | null;
  timestamp: string;
  work?: WorkBrief | null;
}

export interface ReadingStatusResponse {
  id: string;
  user_profile: string;
  work_id: string;
  status: string;
  current_rating?: number | null;
  last_event_at?: string | null;
}

// --- Flag types ---

export interface FlagSummary {
  flag_id: string;
  entity_type: string;
  entity_id: string;
  flag_type: string;
  description: string;
  suggested_fix?: string | null;
  status: string;
  created_at?: string | null;
  resolved_at?: string | null;
}

export interface FlagUpdate {
  action: 'resolve' | 'dismiss';
  applied_fix?: string | null;
}

// --- Search types ---

export interface SearchResults {
  artifacts: ArtifactBrief[];
  works: WorkBrief[];
  creators: CreatorBrief[];
  collections: CollectionBrief[];
  arcs: ArcBrief[];
}

// --- Enums ---

export const ARTIFACT_FORMATS = [
  'Hardcover', 'Paperback', 'Comic Issue', 'Graphic Novel',
  'Magazine', 'Kindle', 'Audible',
] as const;

export const LOCATIONS = [
  'Large Shelf', 'Small Shelf', 'Box', 'Lent', 'Missing', 'Digital',
] as const;

export const READING_STATUSES = ['Unread', 'Reading', 'Finished', 'DNF'] as const;

export const WORK_TYPES = [
  'Novel', 'Non-fiction', 'Hindi Literature',
  'Comic Story', 'Magazine Issue', 'Short Story',
] as const;

export const OWNERS = ['The Bansal Brothers', 'Somdutta'] as const;

export const PROFILES = ['Utsav', 'Utkarsh', 'Som'] as const;

export type ArtifactFormat = typeof ARTIFACT_FORMATS[number];
export type Location = typeof LOCATIONS[number];
export type ReadingStatus = typeof READING_STATUSES[number];
export type WorkType = typeof WORK_TYPES[number];
export type Owner = typeof OWNERS[number];
export type Profile = typeof PROFILES[number];

// --- Paginated response ---

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
}
