export type GpsType = 'ok' | 'zero' | 'none'

export interface Photo {
  id: number
  filename: string
  original_name: string
  album_id: number | null
  exif_lat: number | null
  exif_lng: number | null
  manual_lat: number | null
  manual_lng: number | null
  lat: number | null
  lng: number | null
  gps_type: GpsType
  location_name: string | null
  location_source: 'exif' | 'manual' | 'ai' | null
  taken_at: string | null
  uploaded_at: string
}

export interface Album {
  id: number
  name: string
  description: string
  created_at: string
  photo_count: number
}
