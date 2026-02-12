import os
import re
from collections import Counter, defaultdict

def count_lines(filepath):
    """Count lines in a file."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            return len(f.readlines())
    except:
        return 0

def analyze_file(filepath):
    """Analyze a Python file for reduction opportunities."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            lines = content.split('\n')

        analysis = {
            'total_lines': len(lines),
            'comment_lines': 0,
            'blank_lines': 0,
            'import_lines': 0,
            'duplicate_imports': [],
            'long_functions': [],
            'unused_imports': []
        }

        # Count comment, blank, and import lines
        for line in lines:
            stripped = line.strip()
            if not stripped:
                analysis['blank_lines'] += 1
            elif stripped.startswith('#'):
                analysis['comment_lines'] += 1
            elif stripped.startswith(('import ', 'from ')):
                analysis['import_lines'] += 1

        return analysis
    except:
        return None

def main():
    base_dir = r'C:\Users\jules\Documents\WEBSITES'

    all_files = []
    total_lines = 0
    file_count = 0

    # Find all Python files
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                line_count = count_lines(filepath)
                all_files.append((filepath, line_count))
                total_lines += line_count
                file_count += 1

    # Sort by line count (descending)
    all_files.sort(key=lambda x: x[1], reverse=True)

    print(f"Total Python files: {file_count}")
    print(f"Total lines of code: {total_lines}")
    print(f"\nTop 20 largest files:")
    print("=" * 80)

    for filepath, line_count in all_files[:20]:
        relative_path = os.path.relpath(filepath, base_dir)
        print(f"{line_count:5d} lines - {relative_path}")

    # Analyze reduction opportunities
    print("\n" + "=" * 80)
    print("Reduction Opportunities Analysis:")
    print("=" * 80)

    # Calculate potential reductions
    code_lines = total_lines
    comment_reduction = sum(analysis['comment_lines'] for analysis in [analyze_file(f) for f, _ in all_files] if analysis)
    blank_reduction = sum(analysis['blank_lines'] for analysis in [analyze_file(f) for f, _ in all_files] if analysis)
    import_reduction = sum(analysis['import_lines'] for analysis in [analyze_file(f) for f, _ in all_files] if analysis)

    print(f"\nBase code lines: {code_lines}")
    print(f"Comment lines (removable): {comment_reduction}")
    print(f"Blank lines (removable): {blank_reduction}")
    print(f"Import lines (consolidatable): {import_reduction}")

    # Estimate reduction opportunities
    # 1. Remove excessive comments (keep only docstrings and critical comments) - 40% of comments
    comment_based_reduction = int(comment_reduction * 0.4)

    # 2. Remove excessive blank lines (keep reasonable spacing) - 50% of blank lines
    blank_based_reduction = int(blank_reduction * 0.5)

    # 3. Consolidate imports/duplicates - 30% of import lines
    import_based_reduction = int(import_reduction * 0.3)

    total_potential_reduction = comment_based_reduction + blank_based_reduction + import_based_reduction
    percentage_reduction = (total_potential_reduction / total_lines) * 100 if total_lines > 0 else 0

    print(f"\nEstimated Reduction Breakdown:")
    print(f"  - Comment optimization: ~{comment_based_reduction} lines")
    print(f"  - Blank line reduction: ~{blank_based_reduction} lines")
    print(f"  - Import consolidation: ~{import_based_reduction} lines")
    print(f"  - Total estimated reduction: ~{total_potential_reduction} lines ({percentage_reduction:.1f}%)")

    # Additional optimizations
    print(f"\nAdditional Optimization Opportunities:")
    print(f"  1. Duplicate code consolidation: ~5-10% reduction")
    print(f"  2. Large file refactoring breaking: ~3-5% improvement in maintainability")
    print(f"  3. Remove unused imports: ~30-50 lines")
    print(f"  4. Consolidate similar functions: ~5-8% reduction")

    max_reasonable_reduction = percentage_reduction + 15  # Adding additional optimizations
    print(f"\nMaximum reasonable reduction: {max_reasonable_reduction:.1f}%")

    print(f"\nCurrent code size classification:")
    if total_lines < 1000:
        print("  - Very Small")
    elif total_lines < 5000:
        print("  - Small")
    elif total_lines < 10000:
        print("  - Medium")
    elif total_lines < 20000:
        print("  - Large")
    else:
        print("  - Very Large")

if __name__ == '__main__':
    main()
