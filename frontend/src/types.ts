export type SchemaModel = {
  id?: string;
  name?: string;
  title?: string;
  description?: string;
  prefixes?: Record<string, string>;
  imports?: string[];
  default_prefix?: string;
  default_range?: string;
  types?: Record<string, unknown>;
  annotations?: Record<string, AnnotationValue>;
  classes: Record<string, SchemaClass>;
  slots: Record<string, Slot>;
  enums: Record<string, SchemaEnum>;
};

export type AnnotationValue = string | number | boolean | { value?: string | number | boolean };
export type ProfileTermKind = 'base' | 'profile' | 'extension';
export type RequirementLevel = 'mandatory' | 'recommended' | 'optional' | 'deprecated';
export type ValidationSeverity = 'Violation' | 'Warning' | 'Info';

export type SchemaClass = {
  name?: string;
  title?: string;
  description?: string;
  class_uri?: string;
  is_a?: string;
  slots?: string[];
  annotations?: Record<string, AnnotationValue>;
};

export type Slot = {
  name?: string;
  title?: string;
  description?: string;
  slot_uri?: string;
  range: string;
  required?: boolean;
  multivalued?: boolean;
  annotations?: Record<string, AnnotationValue>;
};

export type SchemaEnum = {
  name?: string;
  permissible_values: Record<string, unknown> | string[];
};

export type SelectedItem =
  | { kind: 'schema'; id: 'schema' }
  | { kind: 'class'; id: string }
  | { kind: 'slot'; id: string; classId?: string }
  | { kind: 'enum'; id: string }
  | null;
