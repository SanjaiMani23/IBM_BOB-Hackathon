import type { ChangedFile } from '../data/mockAnalysis';

interface Props {
  files: ChangedFile[];
  selected: string;
  onSelect: (path: string) => void;
}

function FileIcon({ status }: { status: ChangedFile['status'] }) {
  const color =
    status === 'added' ? 'text-[#198038]' : status === 'deleted' ? 'text-[#DA1E28]' : 'text-[#525252]';
  const label = status === 'added' ? 'A' : status === 'deleted' ? 'D' : 'M';
  return (
    <span className={`font-mono text-[10px] font-semibold w-3 text-right ${color}`}>{label}</span>
  );
}

function buildTree(files: ChangedFile[]) {
  const tree: Record<string, ChangedFile[]> = {};
  files.forEach((f) => {
    const parts = f.path.split('/');
    const dir = parts.slice(0, -1).join('/') || '.';
    if (!tree[dir]) tree[dir] = [];
    tree[dir].push(f);
  });
  return tree;
}

export default function FileExplorer({ files, selected, onSelect }: Props) {
  const tree = buildTree(files);
  const dirs = Object.keys(tree).sort();

  return (
    <div className="h-full overflow-y-auto">
      <div className="px-3 py-2 border-b border-[#D0D0D0]">
        <span className="text-label">Changed Files</span>
        <span className="ml-2 font-mono text-xs text-[#0F62FE]">{files.length}</span>
      </div>
      <div className="py-1">
        {dirs.map((dir) => (
          <div key={dir}>
            <div className="px-3 py-1 font-mono text-[11px] text-[#525252] bg-[#F4F4F4] border-b border-[#E0E0E0]">
              {dir}/
            </div>
            {tree[dir].map((file) => {
              const filename = file.path.split('/').pop()!;
              const isSelected = selected === file.path;
              return (
                <button
                  key={file.path}
                  onClick={() => onSelect(file.path)}
                  className={`w-full text-left px-3 py-1.5 flex items-center justify-between gap-2 transition-colors cursor-pointer border-none ${
                    isSelected
                      ? 'bg-[#EDF4FF] border-l-2 border-l-[#0F62FE]'
                      : 'bg-white hover:bg-[#F4F4F4] border-l-2 border-l-transparent'
                  }`}
                >
                  <span className="font-mono text-xs text-[#161616] truncate">{filename}</span>
                  <div className="flex items-center gap-2 shrink-0">
                    <span className="font-mono text-[10px] text-[#198038]">+{file.additions}</span>
                    <span className="font-mono text-[10px] text-[#DA1E28]">-{file.deletions}</span>
                    <FileIcon status={file.status} />
                  </div>
                </button>
              );
            })}
          </div>
        ))}
      </div>
    </div>
  );
}
