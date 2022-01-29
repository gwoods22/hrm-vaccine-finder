<script>
const axios = require('axios');
const Cookies = require('js-cookie')

const AWS_URL = 'https://rxaf4n42ye.execute-api.us-east-2.amazonaws.com/prod/'

const TEST_MODE = true

const headers =  {
  'x-api-key': 'ca7nZ35PtD5lxNQQEW5rE5aP8416btyhce6RJPRa',
  'Content-Type': 'application/json',
  'Test-Mode': TEST_MODE
};

export default {
  name: 'Appts',
  data() {
      return {
        testMode: TEST_MODE,
        hrm: true,  
        isBusy: true,
        loadingDirections: true,
        loadingAppts: true,
        noResults: false,
        lastupdated: '',
        errorMessage: '',
        sortKey: 'utcTime',
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
    let returningUser = true
    if (Cookies.get('returningUser') !== 'true') {
      this.$bvModal.show('help-modal')
      Cookies.set('returningUser', true, { expires: 365 });
      returningUser = false
    } else {
      this.pullData()
    }

    this.$root.$on('bv::modal::hide', bvEvent => {
      if (bvEvent.componentId === 'error-modal' && bvEvent.trigger === 'ok') {
        location.reload();
      }
      if (bvEvent.componentId === 'help-modal' && !returningUser) {
        this.pullData()
      }
    })
  },
  methods: {
    pullData() {
      const vue = this;

      let allLocations =  (new URLSearchParams(window.location.search)).get('all') === 'true';
      if (allLocations) {
        this.sortKey = 'distance'
        this.hrm = false
      }
      
      let url = AWS_URL + 'locations' + window.location.search;
      axios.get(url, {
        'headers': headers
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
          vue.lastupdated = 'Today at ' + time[0]+':'+time[1]+' '+time[2].split(' ')[1].toLowerCase()
          
          let addresses = locations.map(x => ({
            mapsLocationString: x.mapsLocationString,
            id: x.id
          }));
          this.getDistances(addresses)

          let ids = locations.map(x => x.id);
          this.getAppts(ids)
        }
      })
      .catch(error => {
        console.log('Locations request error');
        console.log(error);
      });
    },
    getDistances(addresses) {
      const vue = this;

      let data = {
        // 'home': '5691 Inglis St, Halifax',
        'home': '9830 Main St, Canning',
        'addresses': addresses              
      };

     axios.post(AWS_URL + 'distance', data, {
        'headers': headers
      }).then(response => {
        vue.loadingDirections = false;

        let distances = response.data.distances;

        for (let i=0; i<vue.tableData.length; i++) {
          let dist = distances.find(x => x.id === vue.tableData[i].id);
          vue.tableData[i].distance = dist.distance;
          vue.tableData[i].rawDistance = dist.rawDistance;
        }
        vue.$root.$emit('bv::refresh::table', 'data-table')
      })
      .catch(error => {
        console.log('Distances request error');
        console.log(error);
      });
    },
    getAppts(ids) {
      const vue = this;

      let data = { 
        ids: ids 
      }

      axios.post(AWS_URL + 'appointments', data, {
        'headers': headers
      }).then(response => {
        vue.loadingAppts = false;

        // Error check
        if ('appts' in response.data) {
          let appts = response.data.appts;

          for (let i=0; i<vue.tableData.length; i++) {
            let appt = appts.find(x => x.id === vue.tableData[i].id);
            vue.tableData[i].utcTime = appt.earliest.utcTime;
            vue.tableData[i].apptTime = appt.earliest.apptTime;
            vue.tableData[i].appts = appt.appts;
          }
          vue.$root.$emit('bv::refresh::table', 'data-table')
        } else if (response.data.errorType === 'REQUEST ERROR') {
          console.log(response.data.errorMessage)
          console.log('Appts field:');
          console.log(response.data.appts);
          let problem = vue.tableData.find(x => x.id === response.data.id);
          console.log('Problem location:');
          console.log(problem);
          this.errorMessage = 'This was an error getting the appointment times.'
          this.$bvModal.show('error-modal')
        } else {
          console.log('Error during appointments request');
          console.log(response.data.appts);
          this.errorMessage = 'This was an error getting the appointment times.'
          this.$bvModal.show('error-modal')
        }
      })
      .catch(error => {
        console.log('Locations request error');
        console.log(error);
      }); 
    },
    openModal(id) {
      this.selectedLocation = this.tableData.find(x => x.id === id);
      if (this.selectedLocation.appts.length > 56) {
        this.selectedLocation.appts = this.selectedLocation.appts.slice(0,56)
        this.selectedLocation.appts.push({
          apptTime: 'more...',
          utcTime: '2022-01-01T00:00:00.000Z'
        })
      }
    },
    copyAddress(address) {
      let shortAddress;
      if (address.split(', ').length === 1) {
        shortAddress = address.split(/\s\w+\sNS/)[0]
      } else {
        shortAddress = address.split(', ')[0]
      }

      navigator.clipboard.writeText(shortAddress).then(() => {
        console.log('Async: Copying to clipboard was successful!');
      }, function(err) {
        console.error('Async: Could not copy text: ', err);
      });
    }
  }
}
</script>
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
        This app shows the latest vaccine appointments in the HRM region. Click the
        Earliest Appt. buttons to see all appointments at that location, and click
        the address field to open the location in Google Maps.
      </p>
      <p>
        The copy button makes it easy to quickly copy the appointment address to paste
        it in to the NS reservation site. Then when you search for appointments the
        available one should be right at the top of the results!
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
        As Halifax's vaccine program winds down there are less appointments available.
        To keep this site working as a proof of concept, I've saved past appointment
        data to a database to show how the system works.
      </p>
    </b-alert>
    <p v-if="!loadingDirections && !noResults">Last updated: {{lastupdated}}</p>
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
      >
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
        <!-- Distance header tooltip -->
        <template #head(distance)="data">
          <div class="copy-tootlip">{{ data.label }}
            <span>
              Driving distance calculated from Canning, NS.
            </span>
          </div>
        </template>
        <!-- Copy header tooltip -->
        <template #head(copy)="data">
          <div class="copy-tootlip">{{ data.label }}
            <span>
              The copy button allows you to quickly copy the address for easy pasting
              in to the province's vaccine booking website.
            </span>
          </div>
        </template>
        <!-- Copy address button -->
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
            @click="openModal(data.item.id)" 
            v-b-modal.appt-modal
          >
            {{ data.item.apptTime }}
          </b-button> 
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
<style lang="scss">
  html, body {
    overflow-x: hidden;
  }
  body {
    position: relative
  }
  ul {
    list-style-type: none;
    padding: 0;
  }
  .modal ul {
    max-height: calc(100vh - 15rem);
  }
  tr > td:nth-child(5) button {
    min-width: 8rem;
  }
  li {
    display: inline-block;
    margin: 0 10px;
    width: fit-content;
  }
  td {
    text-align: left;
  }
  footer {
    margin-bottom: 30px;
  }
  .alert-warning {
    display: flex;
    align-items: center;
    svg {
      margin-right: 20px;
    }
    p {
      margin-bottom: 0;
    }
  }
  .table-responsive {
    overflow-x: visible;
  }
  .copy-tootlip {
    position: relative;
    cursor: pointer;
    display: inline-block;

    border-bottom: 1px dotted #888;
    text-decoration: none;
    margin-bottom: -1px;

    &:hover span {
      opacity: 1;
      z-index: 999;
    }
    & span {
      opacity: 0;
      transition: 0.25s;
      position: absolute;
      left: -115px;
      padding: 10px;
      top: 45px;
      width: 270px;
      z-index: -1;
      border-radius: 10px;
      color: #fff;
      background-color: #149baf;

      &::after{
        content: '';
        position: absolute;
        top: -15px;
        left: 50%;
        transform: translateX(-50%);
        width: 0; 
        height: 0; 
        border-left: 15px solid transparent;
        border-right: 15px solid transparent;
        border-bottom: 15px solid #149baf;
      }
    }
  }
  @media (max-width: 480px) {
    .alert-warning {
      display: block;
      text-align: justify;
      & p {
        display: inline;
      }
      & svg {
        margin-right: 10px;
      }
    }
  }
</style>
