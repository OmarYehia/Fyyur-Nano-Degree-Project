#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, jsonify
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
import sys
from flask_migrate import Migrate
from datetime import datetime
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)


#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String())
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    # Changed genres to array to be iterated easily in the future
    genres = db.Column(db.ARRAY(db.String))
    image_link = db.Column(db.String(500))
    website = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean, server_default = 'False')
    seeking_talent_description = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    shows = db.relationship('Show', backref='venue', lazy = True)

class Artist(db.Model):
    __tablename__ = 'artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String())
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String))
    image_link = db.Column(db.String(500))
    website = db.Column(db.String(120))
    facebook_link = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean, server_default = 'False')
    seeking_venue_description = db.Column(db.String(500))
    shows = db.relationship('Show', backref='artist', lazy = True)

class Show(db.Model):
  __tablename__ = 'shows'
  id = db.Column(db.Integer, primary_key = True, nullable = False)
  venue_id = db.Column(db.Integer, db.ForeignKey('venue.id'), nullable = False)
  artist_id = db.Column(db.Integer, db.ForeignKey('artist.id'), nullable = False)
  show_date = db.Column(db.DateTime, nullable = False)

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  
  # This returns distinct pairs [City-State]
  distinct_pairs = Venue.query.distinct(Venue.state, Venue.city).all()
  data = []

  # Loop through each to get all venues
  for area in distinct_pairs:
    venues = Venue.query.filter_by(state = area.state).filter_by(city = area.city).all()
    venue_data = []
    for venue in venues:
      venue_data.append({
        'id' : venue.id,
        'name' : venue.name
      })
    data.append({
      'city' : area.city,
      'state' : area.state,
      'venues' : venue_data
    })
  
  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  search_term = request.form.get('search_term')
  search_results = Venue.query.filter(Venue.name.ilike('%{}%'.format(search_term))).all()
  data = []

  for venue in search_results:
    num_upcoming_shows = len(Show.query.filter(Show.venue_id == venue.id).filter(Show.show_date > datetime.now()).all())
    data.append({
      'id': venue.id,
      'name': venue.name,
      'num_upcoming_shows': num_upcoming_shows
    })

  response = {
    'count': len(search_results),
    'data': data
  }
  return render_template('pages/search_venues.html', results=response, search_term=search_term)

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):

  venue_info = Venue.query.get(venue_id)
  
  # Return a 404 if no Venue matches the ID in the URL
  if not venue_info:
    return render_template('errors/404.html')

  # Queries for upcoming and past shows
  get_upcoming_shows = Show.query.join(Artist).filter(Show.venue_id == venue_id).filter(Show.show_date > datetime.now()).all()
  get_past_shows = Show.query.join(Artist).filter(Show.venue_id == venue_id).filter(Show.show_date < datetime.now()).all()

  upcoming = []
  past = []

  for show in get_upcoming_shows:
    upcoming.append({
      'artist_id' : show.artist_id,
      'artist_name' : show.artist.name,
      'artist_image_link' : show.artist.image_link,
      'start_time' : show.show_date.strftime("%d-%m-%Y (%H:%M)")
    })

  for show in get_past_shows:
    past.append({
      'artist_id' : show.artist_id,
      'artist_name' : show.artist.name,
      'artist_image_link' : show.artist.image_link,
      'start_time' : show.show_date.strftime("%d-%m-%Y (%H:%M)")
    })

  data = {
    'id': venue_id,
    'name': venue_info.name,
    'genres': venue_info.genres,
    'address': venue_info.address,
    'city': venue_info.city,
    'state': venue_info.state,
    'phone': venue_info.phone,
    'website': venue_info.website,
    'facebook_link': venue_info.facebook_link,
    'seeking_talent': venue_info.seeking_talent,
    'seeking_description': venue_info.seeking_talent_description,
    'image_link': venue_info.image_link,
    'past_shows': past,
    'upcoming_shows': upcoming,
    'past_shows_count': len(past),
    'upcoming_shows_count': len(upcoming)
  }

  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  error = False

  # This method is used because BooleanField from WTForms returns the true value a 'y'
  seeking = False
  if request.form.get('seeking_talent') == 'y':
    seeking = True

  try:
    newVenue = Venue(
      name = request.form.get('name'), 
      city = request.form.get('city'),
      state = request.form.get('state'),
      address = request.form.get('address'),
      phone = request.form.get('phone'),
      genres = request.form.getlist('genres'),
      facebook_link = request.form.get('facebook_link'),
      website = request.form.get('website'),
      seeking_talent = seeking,
      seeking_talent_description = request.form.get('seeking_talent_description')
    )

    db.session.add(newVenue)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  if error:
    flash('An error occured while listing Venue: ' + request.form.get('name') + '. Please try again!')
  else:
    # on successful db insert, flash success
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  return redirect(url_for('index'))

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  error = False
  try:
    Venue.query.filter_by(id = venue_id).delete()
    db.session.commit()
  except:
    error = True
    db.session.rollback()
  finally:
    db.session.close
  if error:
    flash(f'An error occured. Venue with ID:{venue_id} could not be deleted. Please try again!')
  else:
    # on successful db insert, flash success
    flash(f'Venue with ID:{venue_id} was successfully deleted!')
  return jsonify({'Success': True})

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  
  artists = Artist.query.all()
  data = []
  for artist in artists:
    data.append({
      'id': artist.id,
      'name': artist.name
    })

  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  search_term = request.form.get('search_term')
  search_results = Artist.query.filter(Artist.name.ilike('%{}%'.format(search_term))).all()
  data = []

  for artist in search_results:
    num_upcoming_shows = len(Show.query.filter(Show.venue_id == artist.id).filter(Show.show_date > datetime.now()).all())
    data.append({
      'id': artist.id,
      'name': artist.name,
      'num_upcoming_shows': num_upcoming_shows
    })

  response = {
    'count': len(search_results),
    'data': data
  }
  return render_template('pages/search_venues.html', results=response, search_term=search_term)
  

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):

  artist_info = Artist.query.get(artist_id)
  
  # Return a 404 if no Artist matches the ID in the URL
  if not artist_info:
    return render_template('errors/404.html')

  # Queries for upcoming and past shows
  get_upcoming_shows = Show.query.join(Venue).filter(Show.venue_id == artist_id).filter(Show.show_date > datetime.now()).all()
  get_past_shows = Show.query.join(Venue).filter(Show.venue_id == artist_id).filter(Show.show_date < datetime.now()).all()

  upcoming = []
  past = []

  for show in get_upcoming_shows:
    upcoming.append({
      'venue_id' : show.venue_id,
      'venue_name' : show.vemue.name,
      'venue_image_link' : show.venue.image_link,
      'start_time' : show.show_date.strftime("%d-%m-%Y (%H:%M)")
    })

  for show in get_past_shows:
    past.append({
      'venue_id' : show.venue_id,
      'venue_name' : show.vemue.name,
      'venue_image_link' : show.venue.image_link,
      'start_time' : show.show_date.strftime("%d-%m-%Y (%H:%M)")
    })

  data = {
    'id': artist_id,
    'name': artist_info.name,
    'genres': artist_info.genres,
    'city': artist_info.city,
    'state': artist_info.state,
    'phone': artist_info.phone,
    'website': artist_info.website,
    'facebook_link': artist_info.facebook_link,
    'seeking_venue': artist_info.seeking_venue,
    'seeking_description': artist_info.seeking_venue_description,
    'image_link': artist_info.image_link,
    'past_shows': past,
    'upcoming_shows': upcoming,
    'past_shows_count': len(past),
    'upcoming_shows_count': len(upcoming)
  }

  return render_template('pages/show_artist.html', artist=data)


#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist = Artist.query.get(artist_id)
  
  # Return a 404 if no Artist matches the ID in the URL
  if not artist:
    return render_template('errors/404.html')

  # Populating the returned form to the user
  form.name.data = artist.name
  form.genres.data = artist.genres
  form.city.data = artist.city
  form.state.data = artist.state
  form.phone.data = artist.phone
  form.website.data = artist.website
  form.facebook_link.data = artist.facebook_link
  form.seeking_venue.data = artist.seeking_venue
  form.seeking_venue_description.data = artist.seeking_venue_description
  form.image_link.data = artist.image_link


  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  error = False
  artist = Artist.query.get(artist_id)

  seeking = False
  if request.form.get('seeking_venue') == 'y':
    seeking = True

  try:
    artist.name = request.form.get('name')
    artist.genres = request.form.getlist('genres')
    artist.city = request.form.get('city')
    artist.state = request.form.get('state')
    artist.phone = request.form.get('phone')
    artist.website = request.form.get('website')
    artist.facebook_link = request.form.get('facebook_link')
    artist.seeking_venue = seeking
    artist.seeking_venue_description = request.form.get('seeking_venue_description')
    artist.image_link = request.form.get('image_link')

    db.session.commit()
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  if error:
    flash('Artist could not be updated!')
  else:
    flash('Artist updated successfuly!')
  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue = Venue.query.get(venue_id)

  # Return a 404 if no Artist matches the ID in the URL
  if not venue:
    return render_template('errors/404.html')

  # Populating the returned form to the user
  form.name.data = venue.name
  form.genres.data = venue.genres
  form.address.data = venue.address
  form.city.data = venue.city
  form.state.data = venue.state
  form.phone.data = venue.phone
  form.website.data = venue.website
  form.facebook_link.data = venue.facebook_link
  form.seeking_talent.data = venue.seeking_talent
  form.seeking_talent_description.data = venue.seeking_talent_description
  form.image_link.data = venue.image_link

  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  error = False
  venue = Venue.query.get(venue_id)

  # This was used becaise the BooleanField in WTForms returns a 'y' or 'n'
  seeking = False
  if request.form.get('seeking_talent') == 'y':
    seeking = True
  
  try:
    venue.name = request.form.get('name')
    venue.genres = request.form.getlist('genres')
    venue.address = request.form.get('address')
    venue.city = request.form.get('city')
    venue.state = request.form.get('state')
    venue.phone = request.form.get('phone')
    venue.website = request.form.get('website')
    venue.facebook_link = request.form.get('facebook_link')
    venue.seeking_talent = seeking
    venue.seeking_talent_description = request.form.get('seeking_talent_description')
    venue.image_link = request.form.get('image_link')

    db.session.commit()
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  if error:
    flash('Venue could not be updated!')
  else:
    flash('Venue was successfuly updated!')
  
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  error = False
  seeking = False
  if request.form.get('seeking_venue') == 'y':
    seeking = True
  try:
    newArtist = Artist(
      name = request.form.get('name'), 
      city = request.form.get('city'),
      state = request.form.get('state'),
      phone = request.form.get('phone'),
      genres = request.form.getlist('genres'),
      facebook_link = request.form.get('facebook_link'),
      website = request.form.get('website'),
      seeking_venue = seeking,
      seeking_venue_description = request.form.get('seeking_venue_description')
    )

    db.session.add(newArtist)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  if error:
    flash('An error occured while listing artist: ' + request.form.get('name') + '. Please try again!')
  else:
    # on successful db insert, flash success
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  return redirect(url_for('index'))


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():

  shows_info = Show.query.all()
  data = []

  for show in shows_info:
    data.append({
      'venue_id': show.venue_id,
      'venue_name': show.venue.name,
      'artist_id': show.artist_id,
      'artist_name': show.artist.name,
      'artist_image_link': show.artist.image_link,
      # strftime() is used to parse the date time into a string
      'start_time': show.show_date.strftime("%d-%m-%Y (%H:%M)")
    })
    
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  error = False
  try:
    newShow = Show(
      venue_id = request.form.get('venue_id'),
      artist_id = request.form.get('artist_id'),
      show_date = request.form.get('start_time')
    )
    db.session.add(newShow)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  if error:
    flash('Something went wrong! Show could not be submitted!')
  else:
    # on successful db insert, flash success
    flash('Show was successfully listed!')
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
