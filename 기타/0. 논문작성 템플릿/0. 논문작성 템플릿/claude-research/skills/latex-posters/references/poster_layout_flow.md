# Visual Flow and Reading Patterns

> Eye movement patterns (Z, F, Gutenberg) and directional cues for poster layouts.
> See also: [poster_layout_grids.md](poster_layout_grids.md) for grid systems and column layouts.

## Visual Flow and Reading Patterns

### Z-Pattern (Landscape Posters)

Viewers' eyes naturally follow a Z-shape on landscape layouts:

```
START → → → → → → → → → → → → → → TOP RIGHT
  ↓                                    ↓
  ↓                                    ↓
MIDDLE LEFT → → → → → → → → → MIDDLE RIGHT
  ↓                                    ↓
  ↓                                    ↓
BOTTOM LEFT → → → → → → → → → → → → END
```

**Design Strategy**:
1. **Top-left**: Title and introduction (entry point)
2. **Top-right**: Institution logo, QR code
3. **Center**: Key result or main figure
4. **Bottom-right**: Conclusions and contact (exit point)

**Content Placement**:
- Critical information at corners and center
- Support information along diagonal paths
- Use arrows or visual cues to reinforce flow

### F-Pattern (Portrait Posters)

Portrait posters follow F-shaped eye movement:

```
TITLE → → → → → → → → → → → →
  ↓
INTRO → → → →
  ↓
METHODS
  ↓
RESULTS → → →
  ↓
RESULTS (cont.)
  ↓
DISCUSSION
  ↓
CONCLUSIONS → → → → → → → → →
```

**Design Strategy**:
1. Place engaging content at top-left
2. Use section headers to create horizontal scan points
3. Most important figures in upper-middle area
4. Conclusions visible without scrolling (if digital) or from distance

### Gutenberg Diagram

Classic newspaper layout principle:

```
+------------------+------------------+
| PRIMARY AREA     | STRONG FALLOW    |
| (most attention) | (moderate attn)  |
|   ↓              |        ↓         |
+------------------+------------------+
| WEAK FALLOW      | TERMINAL AREA    |
| (least attention)| (final resting)  |
|                  |        ↑         |
+------------------+------------------+
```

**Optimization**:
- **Primary Area** (top-left): Introduction, problem statement
- **Strong Fallow** (top-right): Supporting figure, logo
- **Weak Fallow** (bottom-left): Methods details, references
- **Terminal Area** (bottom-right): Conclusions, take-home message

### Directional Cues

Guide viewers explicitly through content:

**Numerical Ordering**:
```latex
\block{❶ Introduction}{...}
\block{❷ Methods}{...}
\block{❸ Results}{...}
\block{❹ Conclusions}{...}
```

**Arrows and Lines**:
```latex
\begin{tikzpicture}
  \node[block] (intro) {Introduction};
  \node[block, right=of intro] (methods) {Methods};
  \node[block, right=of methods] (results) {Results};
  \draw[->, thick, blue] (intro) -- (methods);
  \draw[->, thick, blue] (methods) -- (results);
\end{tikzpicture}
```

**Color Progression**:
- Light to dark shades indicating progression
- Cool to warm colors showing importance increase
- Consistent color for related sections
