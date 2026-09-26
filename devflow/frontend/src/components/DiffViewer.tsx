import type { DiffLine } from '../data/mockAnalysis';

interface Props {
  lines: DiffLine[];
  filename: string;
}

export default function DiffViewer({ lines, filename }: Props) {
  return (
    <div className="h-full flex flex-col overflow-hidden">
      <div className="px-3 py-2 border-b border-[#D0D0D0] flex items-center justify-between bg-[#1C1C1C] shrink-0">
        <span className="font-mono text-xs text-[#A8A8A8]">{filename}</span>
        <div className="flex items-center gap-3">
          <span className="text-[10px] font-mono text-[#198038]">+{lines.filter(l => l.type === 'add').length}</span>
          <span className="text-[10px] font-mono text-[#DA1E28]">-{lines.filter(l => l.type === 'remove').length}</span>
        </div>
      </div>
      <div className="flex-1 overflow-y-auto bg-[#161616]">
        <table className="w-full border-collapse text-xs font-mono">
          <tbody>
            {lines.map((line, i) => {
              if (line.type === 'header') {
                return (
                  <tr key={i} className="bg-[#252525]">
                    <td className="w-8 text-right px-2 py-0.5 text-[#525252] select-none border-r border-[#333]" />
                    <td className="px-3 py-0.5 text-[#6F6F6F]">{line.content}</td>
                  </tr>
                );
              }
              const bgClass =
                line.type === 'add' ? 'bg-[#022D0D]' :
                line.type === 'remove' ? 'bg-[#2D0709]' :
                '';
              const textClass =
                line.type === 'add' ? 'text-[#42BE65]' :
                line.type === 'remove' ? 'text-[#FF8389]' :
                'text-[#C6C6C6]';
              const prefix =
                line.type === 'add' ? '+' :
                line.type === 'remove' ? '-' :
                ' ';
              return (
                <tr key={i} className={`${bgClass} hover:brightness-125 transition-all`}>
                  <td className={`w-8 text-right px-2 py-0.5 text-[#525252] select-none border-r border-[#2A2A2A]`}>
                    {line.lineNum}
                  </td>
                  <td className={`px-3 py-0.5 ${textClass} whitespace-pre`}>
                    <span className="select-none opacity-60 mr-1">{prefix}</span>
                    {line.content.replace(/^[+\-]/, '')}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
