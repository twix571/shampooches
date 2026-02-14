# Shampooches Global Color System

## Overview
This document describes the global color system used throughout the Shampooches application. All colors are defined as CSS variables in `mainapp/templates/mainapp/base.html` and can be easily modified for theming.

## Color Philosophy
- **Semantic naming**: Colors are named by purpose (e.g., `text-gray`, `error-text`) not by appearance
- **Centralized definitions**: All colors defined once in `:root` CSS variables
- **Tailwind integration**: Semantic colors accessible via Tailwind config extension
- **Easy theming**: Change variables in one place to update entire app

## CSS Variables Reference

### Brand Colors
- `--gold-100`: `#FEFDF5` - Lightest gold (backgrounds)
- `--gold-200`: `#FDF6CC` - Light gold (hover states)
- `--gold-300`: `#FAED99` - Medium light gold
- `--gold-500`: `#D4AF37` - Primary gold accent
- `--gold-700`: `#967D21` - Dark gold
- `--gold-1000`: `#1E3A52` - Primary dark (buttons, text)

### Semantic Theme Colors
- `--primary-dark`: `--gold-1000` - Primary dark accent
- `--primary-black`: `#0F172A` - Primary black text
- `--dark-gray`: `#374151` - Secondary dark text
- `--text-gray`: `#6B7280` - Tertiary gray text
- `--light-gold`: `#FEFDF5` - Light gold background

### Status Colors
**Success (Revenue, Available Slots, Completed)**
- `--success-bg`: `#F0FDF4`
- `--success-border`: `#16A34A`
- `--success-text`: `#16A34A`

**Warning (Pending, Alerts)**
- `--warning-bg`: `#FEFCE8`
- `--warning-border`: `#CA8A04`
- `--warning-text`: `#CA8A04`

**Error (Danger, Delete)**
- `--error-bg`: `#FEF2F2`
- `--error-border`: `#DC2626`
- `--error-text`: `#DC2626`

**Info**
- `--info-bg`: `#F9FAFB`
- `--info-border`: `#4B5563`
- `--info-text`: `#1F2937`

### Neutral Scale
- `--gray-50` to `--gray-900`: Full grayscale for backgrounds, borders, text

### Accent Colors
- `--green-50`, `--green-500/600/700`: For success states, revenue indicators
- `--blue-50/500/600/700/800`: For primary actions, today highlights
- `--purple-50/500/600`: For revenue metrics
- `--amber-50/500/600/700/800/900`: For warnings, pending states
- `--red-500/600`: For error states, dangerous actions

## Usage Patterns

### Standard Tailwind Colors
For standard UI components, continue using Tailwind's built-in colors:
```html
<div class="text-gray-800">Standard text</div>
<div class="bg-gray-50">Light background</div>
<div class="border-gray-200">Subtle border</div>
```

### Semantic Theme Colors (CSS Variables)
For brand-specific theming:
```html
<div style="color: var(--text-gray)">Theme text</div>
<div style="background: var(--light-gold)">Light gold background</div>
<button class="text-white bg-[var(--primary-dark)]">Primary button</button>
```

### Status Colors (Use Variables)
For status messages and alerts:
```html
<!-- Django messages -->
<div class="px-4 py-3 rounded-lg alert-{{ message.tags }}">
  Content
</div>

<!-- Custom status elements -->
<div style="background: var(--success-bg); border-color: var(--success-border);">
  Success message
</div>
```

## Tailwind Configuration

Semantic colors are available as Tailwind utilities:
```javascript
colors: {
    'primary-dark': 'var(--primary-dark)',
    'primary-black': 'var(--primary-black)',
    'dark-gray': 'var(--dark-gray)',
    'text-gray': 'var(--text-gray)',
    'light-gold': 'var(--light-gold)',
}
```

Usage:
```html
<div class="text-primary-black">Text with semantic color</div>
<div class="bg-light-gold">Background with semantic color</div>
```

## Gold Color Palette

The primary brand color is Gold, with these Tailwind utilities:
- `gold-100` to `gold-900`: Standard gold scale
- `gold-1000`: Custom primary dark for buttons

Usage:
```html
<button class="text-white bg-gold-1000 hover:bg-gold-600">
  Gold Button
</button>
<div class="border-l-4 border-gold-1000">
  Gold accent border
</div>
```

## Status Message System

Django messages automatically use color variables via `.alert-*` classes:
```css
.alert-error    { border-color: var(--error-border); background: var(--error-bg); }
.alert-success  { border-color: var(--success-border); background: var(--success-bg); }
.alert-warning  { border-color: var(--warning-border); background: var(--warning-bg); }
.alert-info     { border-color: var(--info-border); background: var(--info-bg); }
```

## Future Improvements

### Incremental Migration
To further reduce hardcoding:
1. Identify frequently repeated color patterns
2. Create semantic utility classes
3. Replace hardcoded classes incrementally

Example migration:
```html
<!-- Before -->
<div class="text-green-600 bg-green-50 border border-green-200">
<div class="text-amber-600 bg-amber-50 border border-amber-200">

<!-- After -->
<div class="status-message status-success">
<div class="status-message status-warning">
```

### Dark Mode Support
The current CSS variable system supports future dark mode via CSS media queries:
```css
:root {
    --primary-black: #0F172A;  /* Light mode */
}
@media (prefers-color-scheme: dark) {
    :root {
        --primary-black: #F9FAFB;  /* Dark mode */
    }
}
```

## Color Semantics

### Revenue / Money
- Green backgrounds/text: `--success-*`, `--green-*`

### Pending / Awaiting
- Amber backgrounds/text: `--warning-*`, `-- amber-*`

### Completed / Success
- Green backgrounds/text: `--success-*`, `--green-*`

### Errors / Danger
- Red backgrounds/text: `--error-*`, `--red-*`

### Primary Actions
- Gold dark: `--primary-dark`, `gold-1000`
- Hover: `gold-600`

### Text Hierarchy
- Primary headings: `--primary-black`, text-gray-800
- Secondary text: `--dark-gray`, text-gray-700
- Tertiary text: `--text-gray`, text-gray-600
- Muted text: text-gray-400/500

## Implementation Checklist

When adding new UI components:
- [ ] Check existing color patterns in similar components
- [ ] Use semantic CSS variables for theme-related colors
- [ ] Use standard Tailwind utilities for common UI elements
- [ ] Document any new color usage patterns

## Changelog

### February 13, 2026
- Created comprehensive CSS variable system
- Added semantic naming for brand colors
- Centralized status colors (success/warning/error/info)
- Documented color system for future reference
- Foundation laid for easy theming and dark mode
