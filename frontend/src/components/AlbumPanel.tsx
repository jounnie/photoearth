import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getAlbums, createAlbum, deleteAlbum, assignAlbum } from '../api/client'
import type { Album } from '../types'

const DRAG_TYPE = 'application/photoearth-ids'

interface Props {
  selectedAlbumId: number | null
  selectedIds: Set<number>
  onSelect: (id: number | null) => void
  onClearSelection: () => void
}

export function AlbumPanel({ selectedAlbumId, selectedIds, onSelect, onClearSelection }: Props) {
  const qc = useQueryClient()
  const [newName, setNewName] = useState('')
  const [dragOverId, setDragOverId] = useState<number | null>(null)

  const { data: albums = [] } = useQuery({ queryKey: ['albums'], queryFn: getAlbums })

  const createMut = useMutation({
    mutationFn: () => createAlbum(newName.trim()),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['albums'] }); setNewName('') },
  })

  const deleteMut = useMutation({
    mutationFn: deleteAlbum,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['albums'] }); onSelect(null) },
  })

  const assignMut = useMutation({
    mutationFn: ({ ids, albumId }: { ids: number[]; albumId: number }) =>
      Promise.all(ids.map(id => assignAlbum(id, albumId))),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['photos'] })
      qc.invalidateQueries({ queryKey: ['albums'] })
      onClearSelection()
    },
  })

  const handleDragOver = (e: React.DragEvent, albumId: number) => {
    if (!e.dataTransfer.types.includes(DRAG_TYPE)) return
    e.preventDefault()
    e.dataTransfer.dropEffect = 'move'
    setDragOverId(albumId)
  }

  const handleDrop = (e: React.DragEvent, albumId: number) => {
    e.preventDefault()
    setDragOverId(null)
    const raw = e.dataTransfer.getData(DRAG_TYPE)
    if (!raw) return
    const ids: number[] = JSON.parse(raw)
    if (ids.length) assignMut.mutate({ ids, albumId })
  }

  return (
    <div className="album-panel">
      <div className="panel-title">Alben</div>

      <button
        className={`album-item ${selectedAlbumId === null ? 'active' : ''}`}
        onClick={() => onSelect(null)}
      >
        <span className="album-icon">📷</span>
        <span className="album-name">Alle Fotos</span>
      </button>

      {albums.map((album: Album) => (
        <div
          key={album.id}
          className={`album-item ${selectedAlbumId === album.id ? 'active' : ''} ${dragOverId === album.id ? 'drag-over' : ''}`}
          onClick={() => onSelect(album.id)}
          onDragOver={e => handleDragOver(e, album.id)}
          onDragLeave={() => setDragOverId(null)}
          onDrop={e => handleDrop(e, album.id)}
        >
          <span className="album-icon">🗂️</span>
          <span className="album-name">{album.name}</span>
          <span className="album-count">{album.photo_count}</span>
          <button
            className="album-delete"
            onClick={e => { e.stopPropagation(); deleteMut.mutate(album.id) }}
            title="Album löschen"
          >✕</button>
        </div>
      ))}

      <form
        className="album-create"
        onSubmit={e => { e.preventDefault(); if (newName.trim()) createMut.mutate() }}
      >
        <input
          value={newName}
          onChange={e => setNewName(e.target.value)}
          placeholder="Neues Album…"
        />
        <button type="submit" disabled={!newName.trim()}>+</button>
      </form>
    </div>
  )
}
