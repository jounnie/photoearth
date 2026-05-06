import { useRef, useState, useEffect } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { uploadPhotos, detectLocation, deletePhoto, assignAlbum, getAlbums } from '../api/client'
import type { Photo, GpsType, Album } from '../types'

const DRAG_TYPE = 'application/photoearth-ids'

const GPS_META: Record<GpsType, { label: string }> = {
  ok:   { label: 'GPS' },
  zero: { label: '0,0' },
  none: { label: 'kein GPS' },
}
const GROUP_LABEL: Record<GpsType, string> = {
  ok:   'GPS vorhanden',
  zero: 'Koordinate 0, 0',
  none: 'Kein GPS',
}
const COORD_TEXT = (p: Photo) => {
  if (p.gps_type === 'ok') return `${p.lat!.toFixed(5)}, ${p.lng!.toFixed(5)}`
  if (p.gps_type === 'zero') return '0.0, 0.0 — ungültig'
  return 'Kein GPS'
}

interface Props {
  photos: Photo[]
  activeId: number | null
  albumId: number | null
  activeFilter: GpsType | 'all'
  selectedIds: Set<number>
  onFilter: (f: GpsType | 'all') => void
  onFocus: (p: Photo) => void
  onToggleSelect: (p: Photo, mode: 'single' | 'toggle' | 'range', allPhotos: Photo[]) => void
  onClearSelection: () => void
}

export function PhotoList({
  photos, activeId, albumId, activeFilter, selectedIds,
  onFilter, onFocus, onToggleSelect, onClearSelection,
}: Props) {
  const qc = useQueryClient()
  const inputRef       = useRef<HTMLInputElement>(null)
  const folderInputRef = useRef<HTMLInputElement>(null)
  const [pickerPhotoId, setPickerPhotoId] = useState<number | null>(null)
  const [draggingIds, setDraggingIds]     = useState<Set<number>>(new Set())

  const { data: albums = [] } = useQuery<Album[]>({ queryKey: ['albums'], queryFn: getAlbums })

  const uploadMut = useMutation({
    mutationFn: (files: File[]) => uploadPhotos(files, albumId ?? undefined),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['photos'] }),
  })
  const aiMut = useMutation({
    mutationFn: detectLocation,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['photos'] }),
  })
  const deleteMut = useMutation({
    mutationFn: deletePhoto,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['photos'] }),
  })
  const assignMut = useMutation({
    mutationFn: ({ id, albumId }: { id: number; albumId: number | null }) => assignAlbum(id, albumId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['photos'] })
      qc.invalidateQueries({ queryKey: ['albums'] })
      setPickerPhotoId(null)
    },
  })

  // Close picker on outside click
  useEffect(() => {
    if (pickerPhotoId === null) return
    const h = () => setPickerPhotoId(null)
    window.addEventListener('click', h)
    return () => window.removeEventListener('click', h)
  }, [pickerPhotoId])

  const counts = { all: photos.length, ok: 0, zero: 0, none: 0 }
  photos.forEach(p => counts[p.gps_type]++)

  const groups: Record<GpsType, Photo[]> = { ok: [], zero: [], none: [] }
  photos.forEach(p => groups[p.gps_type].push(p))

  const handleFileDrop = (e: React.DragEvent) => {
    e.preventDefault()
    const files = Array.from(e.dataTransfer.files).filter(f => f.type.startsWith('image/'))
    if (files.length) uploadMut.mutate(files)
  }

  // ── Drag start ──────────────────────────────────────────────────────────────
  const handleDragStart = (e: React.DragEvent, photo: Photo) => {
    // If this photo isn't selected yet, drag just it (don't mutate global selection)
    const ids = selectedIds.has(photo.id) ? [...selectedIds] : [photo.id]
    setDraggingIds(new Set(ids))
    e.dataTransfer.setData(DRAG_TYPE, JSON.stringify(ids))
    e.dataTransfer.effectAllowed = 'move'

    // Ghost image: show count badge
    const ghost = document.createElement('div')
    ghost.style.cssText = [
      'position:fixed', 'top:-200px', 'left:0',
      'background:#6c8fff', 'color:#fff',
      'padding:4px 10px', 'border-radius:99px',
      'font:600 13px system-ui', 'pointer-events:none',
    ].join(';')
    ghost.textContent = ids.length > 1 ? `${ids.length} Fotos` : photo.original_name
    document.body.appendChild(ghost)
    e.dataTransfer.setDragImage(ghost, ghost.offsetWidth / 2, 16)
    setTimeout(() => ghost.remove(), 0)
  }

  const handleDragEnd = () => setDraggingIds(new Set())

  // ── Click handling ──────────────────────────────────────────────────────────
  const handleItemClick = (e: React.MouseEvent, photo: Photo) => {
    if (e.ctrlKey || e.metaKey) {
      onToggleSelect(photo, 'toggle', photos)
    } else if (e.shiftKey) {
      onToggleSelect(photo, 'range', photos)
    } else {
      onClearSelection()
      onFocus(photo)
    }
  }

  const handleCheckboxClick = (e: React.MouseEvent, photo: Photo) => {
    e.stopPropagation()
    const mode = e.shiftKey ? 'range' : 'toggle'
    onToggleSelect(photo, mode, photos)
  }

  return (
    <div className="photo-list-panel">
      {/* Drop zone */}
      <div className="drop-zone" onDragOver={e => e.preventDefault()} onDrop={handleFileDrop}>
        <span className="drop-icon">📷</span>
        <p><strong>Fotos oder Ordner hierher ziehen</strong></p>
        <div className="drop-actions">
          <button className="drop-btn" onClick={() => inputRef.current?.click()}>Dateien wählen</button>
          <button className="drop-btn" onClick={() => folderInputRef.current?.click()}>Ordner wählen</button>
        </div>
        <input ref={inputRef} type="file" accept="image/*" multiple style={{ display: 'none' }}
          onChange={e => {
            const files = Array.from(e.target.files || []).filter(f => f.type.startsWith('image/'))
            if (files.length) uploadMut.mutate(files)
            e.target.value = ''
          }}
        />
        <input ref={folderInputRef} type="file"
          // @ts-expect-error – non-standard but widely supported
          webkitdirectory="" multiple style={{ display: 'none' }}
          onChange={e => {
            const files = Array.from(e.target.files || []).filter(f => f.type.startsWith('image/'))
            if (files.length) uploadMut.mutate(files)
            e.target.value = ''
          }}
        />
      </div>

      {/* Filter bar */}
      {photos.length > 0 && (
        <div className="filter-bar">
          {(['all', 'ok', 'zero', 'none'] as const).map(f => (
            <button
              key={f}
              className={`filter-btn ${f} ${activeFilter === f ? 'active' : ''}`}
              onClick={() => onFilter(f)}
            >
              {f !== 'all' && <span className="dot" />}
              {f === 'all' ? 'Alle' : GPS_META[f].label}
              <span className="count">{counts[f]}</span>
            </button>
          ))}
        </div>
      )}

      {/* Groups */}
      <div className="photo-list-scroll">
        {photos.length === 0 && (
          <div className="empty-state">
            <div className="empty-icon">🗺️</div>
            <p>Noch keine Fotos geladen</p>
          </div>
        )}

        {(['ok', 'zero', 'none'] as GpsType[]).map(type => {
          const items = groups[type]
          if (items.length === 0) return null
          if (activeFilter !== 'all' && activeFilter !== type) return null
          return (
            <div key={type} className="photo-group">
              <div className={`group-header type-${type}`}>
                <span className="dot" />
                <span>{GROUP_LABEL[type]}</span>
                <span className="g-count">{items.length}</span>
              </div>

              {items.map(photo => {
                const isSelected = selectedIds.has(photo.id)
                const isDragging = draggingIds.has(photo.id)
                return (
                  <div
                    key={photo.id}
                    className={[
                      'photo-item',
                      activeId === photo.id ? 'active' : '',
                      isSelected ? 'selected' : '',
                      isDragging ? 'dragging' : '',
                    ].join(' ')}
                    draggable
                    onDragStart={e => handleDragStart(e, photo)}
                    onDragEnd={handleDragEnd}
                    onClick={e => handleItemClick(e, photo)}
                  >
                    {/* Checkbox */}
                    <div
                      className={`photo-checkbox ${isSelected ? 'checked' : ''}`}
                      onClick={e => handleCheckboxClick(e, photo)}
                    >
                      {isSelected && <span>✓</span>}
                    </div>

                    <img src={`/api/photos/${photo.id}/image`} alt={photo.original_name} />

                    <div className="info">
                      <div className="name">{photo.original_name}</div>
                      <div className="coords">{COORD_TEXT(photo)}</div>
                      {photo.location_name && <div className="location-name">📍 {photo.location_name}</div>}
                    </div>

                    <div className="item-actions">
                      {/* Album picker */}
                      <div className="album-picker-wrap" onClick={e => e.stopPropagation()}>
                        <button
                          className="action-btn album"
                          title="Album zuweisen"
                          onClick={e => {
                            e.stopPropagation()
                            setPickerPhotoId(prev => prev === photo.id ? null : photo.id)
                          }}
                        >🗂️</button>
                        {pickerPhotoId === photo.id && (
                          <div className="album-picker-dropdown">
                            {photo.album_id !== null && (
                              <button className="picker-item remove"
                                onClick={() => assignMut.mutate({ id: photo.id, albumId: null })}
                              >✕ Aus Album entfernen</button>
                            )}
                            {albums.length === 0 && <div className="picker-empty">Noch keine Alben</div>}
                            {albums.map((album: Album) => (
                              <button key={album.id}
                                className={`picker-item ${photo.album_id === album.id ? 'current' : ''}`}
                                onClick={() => assignMut.mutate({ id: photo.id, albumId: album.id })}
                              >{photo.album_id === album.id ? '✓ ' : ''}{album.name}</button>
                            ))}
                          </div>
                        )}
                      </div>

                      {photo.gps_type !== 'ok' && (
                        <button className="action-btn ai" title="Ort via AI erkennen"
                          onClick={e => { e.stopPropagation(); aiMut.mutate(photo.id) }}
                          disabled={aiMut.isPending}
                        >🤖</button>
                      )}
                      <button className="action-btn del" title="Foto löschen"
                        onClick={e => { e.stopPropagation(); deleteMut.mutate(photo.id) }}
                      >✕</button>
                    </div>
                  </div>
                )
              })}
            </div>
          )
        })}
      </div>
    </div>
  )
}
