<script>
const axios = require('axios');
const Cookies = require('js-cookie')

const AWS_URL = 'https://rxaf4n42ye.execute-api.us-east-2.amazonaws.com/prod/'

const TEST_MODE = true
const SAVED_DISTANCES = true

const headers =  {
  'x-api-key': process.env.VUE_APP_API_KEY,
  'Content-Type': 'application/json',
};

export default {
  name: 'Appts',
  data() {
      return {
        testMode: TEST_MODE,
        // return just HRM appts or all of Nova Scotia
        hrm: true,  
        // table waiting for data
        isBusy: true,
        loadingDirections: true,
        loadingAppts: true,
        noResults: false,
        lastUpdated: '',
        // popup modal error message
        errorMessage: '',
        // table sort key
        sortKey: 'utcTime',
        // specified location used to load appointment modal data
        selectedLocation: {},
        tableData: [],
        fields: [
          {
            key: 'shortName',
            label: 'Name',
          },
          'address',
          'copy',
          {
            key: 'distance',
            sortable: true,
          },
          {
            key: 'utcTime',
            sortable: true,
            label: 'Earliest Appt.'
          },
          {
            key: 'vaccine',
            sortable: true
          },
          'age',
        ]
      }
  },
  props: {},
  mounted () {    
    if (Cookies.get('returningUser') !== 'true') {
      this.$bvModal.show('help-modal')
      Cookies.set('returningUser', true, { expires: 365 });
    } else {
      this.getLocations()
    }

    this.$root.$on('bv::modal::hide', bvEvent => {
      if (bvEvent.componentId === 'error-modal' && bvEvent.trigger === 'ok') {
        location.reload();
      }
      if (bvEvent.componentId === 'help-modal') {
        this.getLocations()
      }
    })
  },
  methods: {
    /** 
     * Get vaccine appointment locations in the region
     */
    getLocations() {
      const vue = this;

      let allLocations =  (new URLSearchParams(window.location.search)).get('all') === 'true';
      if (allLocations) {
        this.sortKey = 'distance'
        this.hrm = false
      }
      
      axios.get(AWS_URL + 'locations', {
        'headers': {
          ...headers,
          'Test-Mode': TEST_MODE,
          'All-Locations': allLocations
        }
      }).then(response => {
        console.log(response.data);
        let locations = response.data.locations;
        vue.isBusy = false;
        if (locations.length === 0) {
          vue.loadingDirections = false;
          vue.loadingAppts = false;
          vue.noResults = true;
        } else {
          vue.tableData = locations;

          let now = new Date
          let time = now.toLocaleString().split(', ')[1].split(':')      
          vue.lastUpdated = 'Today at ' + time[0]+':'+time[1]+' '+time[2].split(' ')[1].toLowerCase()
          
          let addresses = locations.map(x => ({
            mapsLocationString: x.mapsLocationString,
            id: x.id
          }));
          this.getDistances(addresses)

          let ids = locations.map(x => x.id);
          this.getAppointments(ids)
        }
      })
      .catch(error => {
        console.log('Locations request error');
        console.log(error);
      });
    },
    /**
     * Get driving distances between home address and each passed address
     *
     * @param {object[]} addresses Array of address objects
     */
    getDistances(addresses) {
      const vue = this;

      let data = {
        'home': '5691 Inglis St, Halifax',
        'addresses': addresses              
      };

     axios.post(AWS_URL + 'distances', data, {
        'headers': {
          ...headers,
          'Saved-Distances': SAVED_DISTANCES
        }
      }).then(response => {
        vue.loadingDirections = false;

        let distances = response.data.distances;

        for (let i=0; i<vue.tableData.length; i++) {
          let dist = distances.find(x => x.id === vue.tableData[i].id);
          vue.tableData[i].distance = dist.distance;
          vue.tableData[i].rawDistance = dist.rawDistance;
        }
      })
      .catch(error => {
        console.log('Distances request error');
        console.log(error);
      });
    },
    /**
     * Get appointment times for passed vaccine locations
     *
     * @param {string[]} ids Array of location IDs
     */
    getAppointments(ids) {
      const vue = this;

      let data = { 
        ids: ids 
      }

      axios.post(AWS_URL + 'appointments', data, {
        'headers': {
          ...headers,
          'Test-Mode': TEST_MODE,
        }
      }).then(response => {
        vue.loadingAppts = false;

        // Error check
        if ('allAppts' in response.data) {
          let appts = response.data.allAppts;

          for (let i=0; i<vue.tableData.length; i++) {
            let appt = appts.find(x => x.id === vue.tableData[i].id);
            vue.tableData[i].utcTime = appt.earliest.utcTime;
            vue.tableData[i].apptTime = appt.earliest.apptTime;
            vue.tableData[i].appts = appt.appts;
          }
        } else if (response.data.errorType === 'REQUEST ERROR') {
          console.log(response.data.errorMessage)
          console.log('Appts field:');
          console.log(response.data.appts);
          let problemLocation = vue.tableData.find(x => x.id === response.data.id);
          console.log('Problem location:');
          console.log(problemLocation);
          this.errorMessage = 'There was an error getting the appointment times.'
          this.$bvModal.show('error-modal')
        } else {
          console.log('Error during appointments request');
          console.log(response.data.appts);
          this.errorMessage = 'There was an error getting the appointment times.'
          this.$bvModal.show('error-modal')
        }
      })
      .catch(error => {
        console.log('Appointments request error');
        console.log(error);
      }); 
    },
    /**
     * Open modal containing appointment times
     * 
     * If there are more appointments than can fit in the modal,
     * truncate appointments list and add a 'more...' dummy time.
     *
     * @param {number} id ID of the location to display appointments
     */
    openApptModal(id) {
      this.selectedLocation = this.tableData.find(x => x.id === id);
      if (this.selectedLocation.appts.length > 62) {
        this.selectedLocation.appts = this.selectedLocation.appts.slice(0,62)
        this.selectedLocation.appts.push({
          apptTime: 'more...',
          utcTime: ''
        })
      }
    },    
    /**
     * Shorten full address to street address and copy to clipboard
     *
     * @param {string} address Full postal address
     */
    copyAddress(address) {
      let shortAddress;
      if (address.split(', ').length === 1) {
        shortAddress = address.split(/\s\w+\sNS/)[0]
      } else {
        shortAddress = address.split(', ')[0]
      }

      navigator.clipboard.writeText(shortAddress).then(() => {
        console.log('Async: Copying to clipboard was successful!');
      }, err => {
        console.error('Async: Could not copy text: ', err);
      });
    }
  }
}
</script>
<style lang="scss" scoped>
 @import '../assets/Appts.scss';
</style>
<template>
<div>
  <b-modal 
    ok-only
    id="appt-modal" 
    :title="selectedLocation.shortName"
  >
    <ul class="d-flex flex-column flex-wrap">
      <li v-for="item in selectedLocation.appts" :key="item.utcTime">
        {{ item.apptTime }}
      </li>
    </ul>
    <template #modal-footer>
      <div class="w-100 d-flex justify-content-between align-items-center">
        <a 
          target="_blank" 
          rel="noopener noreferrer" 
          href="https://novascotia.flow.canimmunize.ca/en/9874123-19-7418965" 
          class="float-left"
        >
          Book your appointment now!
        </a>
        <b-button
          variant="info"
          class="float-right"
          @click="$bvModal.hide('appt-modal')"
        >
          OK
        </b-button>
      </div>
    </template>
  </b-modal>

  <b-modal 
    ok-only 
    ok-title="Refresh"
    ok-variant="info"
    id="error-modal" 
    title="This doesn't normally happen..."
  >
    <div>
      <p>{{errorMessage}}</p>
      <p>Please refresh the page.</p>
    </div>
  </b-modal>

  <b-modal 
    ok-only
    ok-variant="info"
    id="help-modal" 
    title="Welcome fellow vaccine hunter!"
  >
    <div>
      <p>
        This app helps you find the latest vaccine appointments in the Halifax region so you can
        quickly book through the provincial website. Click the teal buttons under "Earliest Appt."
        to view all available times and click the address field to open the location in Google Maps.
      </p>
      <p>Hope this helps you find an appointment!</p>
    </div>
  </b-modal>

  <div class="container">
    <h1>HRM Vaccine Appointments</h1>
    <p>Book online with a N.S Health card <a target="_blank" rel="noopener noreferrer" href="https://novascotia.flow.canimmunize.ca/en/9874123-19-7418965">here</a> or book by phone at <a href="tel:+1-833-797-7772">1-833-797-7772</a>.</p>
    <b-alert show variant="warning" v-bind:class="{ 'd-none': !testMode }">
      <font-awesome-icon icon="exclamation-triangle" />
      <p>
        <span class="font-weight-bold">This data is now out of date.</span>
        As the Halifax region's initial vaccine program winds down, there are less appointments available.
        To keep this app working as a proof of concept, I've saved previous publicly available appointment
        data to a database to show how the system works.
      </p>
    </b-alert>
    <p v-if="!loadingDirections && !noResults">Last updated: {{lastUpdated}}</p>
    <div class="d-flex justify-content-center mb-3" v-if="loadingDirections">
      <span class="mr-3">Getting Distances</span>
      <b-spinner label="Loading..."></b-spinner>
    </div>
    <div class="d-flex justify-content-center mb-3" v-if="loadingAppts">
      <span class="mr-3">Getting Appointment Times</span>
      <b-spinner label="Loading..."></b-spinner>
    </div>
    <div>
      <b-table 
        responsive
        striped
        hover
        ref="table"
        id="data-table"
        :items="tableData"
        :fields="fields"
        :busy="isBusy"
        primary-key="id"
        :sort-by="sortKey"
      >
        <!-- Age column -->
        <template #cell(age)="data">
          <p>
            {{ data.item.maxAge === null ? `${data.item.minAge}+` : `${data.item.minAge} - ${data.item.maxAge}` }}
          </p>
        </template>
        <!-- Address column -->
        <template #cell(address)="data">
          <a 
            :href="'https://www.google.com/maps/search/' + data.value.replace(/\s/g,'+')"
            target="_blank"
            rel="noopener noreferrer"
          >
            {{ data.value }}
          </a>
        </template>
        <!-- Copy address button column -->
        <template #cell(copy)="data">
          <b-button variant="info" size="sm" @click="copyAddress(data.item.address)">
            <font-awesome-icon icon="copy" />
          </b-button>
        </template>
        <!-- Appts column -->
        <template #cell(utcTime)="data">
          <b-button 
            v-if="loadingAppts"
          >
            Loading...
          </b-button> 
          <b-button 
            variant="info"
            size="sm"
            v-if="!loadingAppts" 
            @click="openApptModal(data.item.id)" 
            v-b-modal.appt-modal
          >
            {{ data.item.apptTime }}
          </b-button> 
        </template>
        <!-- Distance header tooltip -->
        <template #head(distance)="data">
          <div class="copy-tooltip">{{ data.label }}
            <span>
              Driving distance calculated from downtown Halifax, NS.
            </span>
          </div>
        </template>
        <!-- Copy header tooltip -->
        <template #head(copy)="data">
          <div class="copy-tooltip">{{ data.label }}
            <span>
              The copy button allows you to quickly copy the address for easy pasting
              into the province's vaccine booking website.
            </span>
          </div>
        </template>
      </b-table>
      <h4 v-if="noResults">No vaccine locations found</h4>
    </div>
  </div>
  <footer class="text-center">
    <p v-if="hrm && false"><a href="/?all=true">See all NS appointments.</a></p>
    <p v-if="!hrm"><a href="/">Just see HRM appointments.</a></p>
    <p>Made by <a target="_blank" rel="noopener noreferrer" href="http://github.com/gwoods22/">Graeme Woods</a></p>
    <router-link to="/privacy">Privacy Policy</router-link>
  </footer>
</div>
</template>
