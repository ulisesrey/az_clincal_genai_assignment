---
name: react-shadcn-beautifier
description: Beautifies, modernizes, and enhances React frontend components using shadcn/ui and Tailwind CSS. Use whenever asked to polish, modernise, redesign, refactor, or improve React UI components and layouts to look professional, accessible, and user-friendly.
---

# React & shadcn/ui UI/UX Beautifier

A comprehensive guide and workflow for transforming existing React components and pages into modern, clean, accessible, and user-friendly interfaces using **shadcn/ui**, **Tailwind CSS**, and **Lucide React** icons.

## Trigger Scenarios

Use this skill when:
* Redesigning, polishing, or beautifying React components, views, or layouts.
* Upgrading unstyled HTML or legacy React code to modern shadcn/ui component primitives (`Button`, `Card`, `Dialog`, `DropdownMenu`, etc.).
* Improving visual hierarchy, color tokens, typography scales, spacing, and micro-interactions in a React codebase.

---

## Pre-Check: Branding & Design Tokens

Before generating or refactoring React code:

1. **Check for Branding / Design Files**:
   * Inspect the repository for company branding files or custom theme tokens (e.g., `BRANDING.md`, `tailwind.config.js`, `globals.css`, or custom CSS variables).
2. **Apply Brand & Theme Rules**:
   * Use existing brand color tokens and design variables if available.
   * Leverage shadcn/ui semantic color tokens (`bg-background`, `text-foreground`, `bg-primary`, `text-primary-foreground`, `border-border`, `text-muted-foreground`) to ensure seamless light/dark mode support.

---

## Core React & shadcn/ui Design Rules

When building or refactoring React components, adhere to these UI/UX standards:

### 1. Component Composition & Primitives
* **Use shadcn/ui Primitives**: Prefer standard composable shadcn components over raw HTML elements (`<Button>` instead of `<button>`, `<Card>` instead of custom div cards, `<Input>` instead of raw `<input>`).
* **Icons**: Always use `lucide-react` icons inside buttons, table actions, headers, and empty states to add visual clarity (e.g., `<Plus className="mr-2 h-4 w-4" />`).
* **Clean Component Structure**: Break large monolithic components into clean sub-components or atomic hooks where appropriate.

### 2. UI/UX & Visual Polish
* **Whitespace & Layout**: Use Tailwind's grid and flexbox utilities with consistent spacing (`gap-4`, `p-6`, `space-y-4`). Avoid cramped layouts.
* **Typography & Hierarchy**: 
  * Use semantic text styles (`text-2xl font-semibold tracking-tight`, `text-sm font-medium text-foreground`, `text-xs text-muted-foreground`).
  * Ensure proper text wrapping and truncation (`truncate`, `line-clamp-2`) for dynamic data.
* **Interactive Feedback**:
  * Ensure all interactive elements include hover, active, and focus states (`transition-colors`, `focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring`).
  * Represent asynchronous actions gracefully with loading spinners (`Loader2` with `animate-spin` class) and disabled button states during mutations/fetches.

### 3. State Handling (Empty, Loading, Error)
* **Empty States**: Never show a blank container. Design structured empty states with an icon, descriptive text, and a clear call-to-action button.
* **Skeleton Loaders**: Use shadcn/ui skeleton components (`<Skeleton className="h-4 w-[250px]" />`) during data fetching instead of abrupt layout shifts.

---

## Execution Workflow

1. **Analyze Existing React Code**: Evaluate current structure, custom styles, props, and UI states.
2. **Check for Branding Assets**: Inspect the workspace for custom design tokens or branding guidelines.
3. **Map to shadcn/ui Primitives**: Identify raw elements and replace them with modular shadcn/ui components.
4. **Refine Tailwind Styling**: Apply proper spacing, semantic color classes, typography, border radiuses (`rounded-lg`), and shadow tokens (`shadow-sm`).
5. **Incorporate Interactivity & Icons**: Add Lucide React icons, hover transitions, and responsive behavior (`sm:flex-row`, etc.).
6. **Validate**: Ensure light/dark mode compatibility via Tailwind/shadcn CSS variables and check accessibility (`aria-*`, keyboard focus rings).

---

## Code Example Comparison

### ❌ Unpolished React Component
```tsx
export function UserCard({ user, onSave }) {
  return (
    <div style={{ background: '#fff', border: '1px solid gray', padding: '10px' }}>
      <h3>{user.name}</h3>
      <p>{user.email}</p>
      <button onClick={onSave} style={{ background: 'blue', color: 'white' }}>Save</button>
    </div>
  );
}
```
### ✅ Modernized React Component (shadcn/ui & Tailwind)
```tsx
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { User, Mail, Save } from "lucide-react";

interface UserCardProps {
  user: { name: string; email: string };
  onSave: () => void;
  isLoading?: boolean;
}

export function UserCard({ user, onSave, isLoading }: UserCardProps) {
  return (
    <Card className="transition-all hover:shadow-md">
      <CardHeader className="pb-3">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10 text-primary">
            <User className="h-5 w-5"/>
          </div>
          <div>
            <CardTitle className="text-base font-semibold">{user.name}</CardTitle>
            <CardDescription className="flex items-center gap-1 text-xs text-muted-foreground">
              <Mail className="h-3.5 w-3.5"/>
              {user.email}
            </CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent className="flex justify-end pt-2">
        <Button className="gap-2" disabled="{isLoading}" onClick="{onSave}" size="sm">
          <Save className="h-4 w-4"/>
          {isLoading ? "Saving..." : "Save changes"}
        </Button>
      </CardContent>
    </Card>
  );
}
```