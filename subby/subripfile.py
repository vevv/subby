from __future__ import annotations

import pysrt


class SubRipFile(pysrt.SubRipFile):
    def export(self, eol: str | None = None) -> str:
        """Exports subtitle as text"""
        output_eol = eol or self.eol
        output_text = ''

        for item in self:
            string_repr = str(item)
            if output_eol != '\n':
                string_repr = string_repr.replace('\n', output_eol)
            output_text += string_repr
            if not string_repr.endswith(2 * output_eol):
                output_text += output_eol

        return output_text

    def __eq__(self, other):
        return self.export(eol='\n') == other.export(eol='\n')
