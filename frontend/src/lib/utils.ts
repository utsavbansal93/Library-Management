import type { ReadingStatus } from '../types';

export function coverUrl(artifactId: string): string {
  return `/api/artifacts/${artifactId}/cover`;
}

export function readingStatusColor(status: ReadingStatus | string): string {
  switch (status) {
    case 'Reading': return 'bg-tertiary-fixed text-on-tertiary-fixed';
    case 'Finished': return 'bg-primary text-on-primary';
    case 'DNF': return 'bg-error text-on-error';
    case 'Unread':
    default: return 'bg-surface-container-highest text-on-surface-variant';
  }
}

export function formatRoleLabel(role: string): string {
  switch (role) {
    case 'Author': return 'Written by';
    case 'Writer': return 'Written by';
    case 'Artist': return 'Art by';
    case 'Inker': return 'Inked by';
    case 'Colorist': return 'Colors by';
    case 'Letterer': return 'Letters by';
    case 'Editor': return 'Edited by';
    case 'Translator': return 'Translated by';
    case 'Narrator/Performer': return 'Narrated by';
    default: return role;
  }
}

export function cn(...classes: (string | false | null | undefined)[]): string {
  return classes.filter(Boolean).join(' ');
}
