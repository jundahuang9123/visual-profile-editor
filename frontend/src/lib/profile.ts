import type { ProfileTermKind, RequirementLevel, SchemaClass, Slot } from '../types';

type TermDef = SchemaClass | Slot;

export function annotationValue(definition: TermDef | undefined, key: string): string | undefined {
  const raw = definition?.annotations?.[key];
  if (raw && typeof raw === 'object' && 'value' in raw) {
    return raw.value === undefined ? undefined : String(raw.value);
  }
  return raw === undefined ? undefined : String(raw);
}

export function termKind(definition: TermDef | undefined, uriKey: 'class_uri' | 'slot_uri'): ProfileTermKind {
  const annotated = annotationValue(definition, 'term_kind');
  if (annotated === 'base' || annotated === 'profile' || annotated === 'extension') return annotated;
  const uri = String((definition as Record<string, unknown> | undefined)?.[uriKey] ?? '');
  return uri.startsWith('cx:') || uri.startsWith('https://w3id.org/cx#') ? 'extension' : 'base';
}

export function requirementLevel(definition: TermDef | undefined): RequirementLevel | undefined {
  const value = annotationValue(definition, 'requirement_level');
  if (value === 'mandatory' || value === 'recommended' || value === 'optional' || value === 'deprecated') return value;
  return undefined;
}

export function setAnnotation<T extends TermDef>(definition: T, key: string, value: string | undefined): T {
  const annotations = { ...(definition.annotations ?? {}) };
  if (value === undefined || value === '') {
    delete annotations[key];
  } else {
    annotations[key] = { value };
  }
  return { ...definition, annotations } as T;
}

export function profileNameFor(baseName: string, existing: string[]) {
  const base = baseName.endsWith('Profile') ? baseName : `${baseName}Profile`;
  if (!existing.includes(base)) return base;
  let index = 2;
  while (existing.includes(`${base}${index}`)) index += 1;
  return `${base}${index}`;
}
