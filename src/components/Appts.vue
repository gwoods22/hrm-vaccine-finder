<script>
const request = require('request');

const AWS_URL = 'https://rxaf4n42ye.execute-api.us-east-2.amazonaws.com/prod/'

const headers =  {
  'x-api-key': 'ca7nZ35PtD5lxNQQEW5rE5aP8416btyhce6RJPRa',
  'Content-Type': 'application/json'
};

export default {
  name: 'HelloWorld',
  data() {
      return {
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
        ]
      }
  },
  props: {},
  mounted () {
    this.$root.$on('bv::modal::hide', bvEvent => {
      if (bvEvent.componentId === 'error-modal' && bvEvent.trigger === 'ok') {
        location.reload();
      }
    })

    const vue = this;
    let allLocations =  (new URLSearchParams(window.location.search)).get('all') === 'true';
    if (allLocations) {
      this.sortKey = 'distance'
      this.hrm = false
    }
    
    request.get({
      'headers': headers,
      'url': AWS_URL + 'locations' + window.location.search
    }, (error, response) => {
      if (error) throw new Error(error);
      
      let locations = JSON.parse(response.body).locations;
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
  },
  methods: {
    getDistances(addresses) {
      const vue = this;

      let body = { 
        addresses: addresses,
        home: '5691 Inglis St, Halifax'
      }

      request.post({
        'headers': headers,
        'url': AWS_URL + 'distance',
        'body': body,
        'json': true
      }, (error, response) => {
        if (error) throw new Error(error);
        vue.loadingDirections = false;

        let distances = response.body.distances;

        for (let i=0; i<vue.tableData.length; i++) {
          let dist = distances.find(x => x.id === vue.tableData[i].id);
          vue.tableData[i].distance = dist.distance;
          vue.tableData[i].rawDistance = dist.rawDistance;
        }
        vue.$root.$emit('bv::refresh::table', 'data-table')
      });  
    },
    getAppts(ids) {
      const vue = this;

      let body = { 
        ids: ids 
      }

      request.post({
        'headers': headers,
        'url': AWS_URL + 'appointments',
        'body': body,
        'json': true
      }, (error, response) => {
        if (error) throw new Error(error);
        vue.loadingAppts = false;

        // Error check
        if ('appts' in response.body) {
          let appts = response.body.appts;

          for (let i=0; i<vue.tableData.length; i++) {
            let appt = appts.find(x => x.id === vue.tableData[i].id);
            vue.tableData[i].utcTime = appt.earliest.utcTime;
            vue.tableData[i].apptTime = appt.earliest.apptTime;
            vue.tableData[i].appts = appt.appts;
          }
          vue.$root.$emit('bv::refresh::table', 'data-table')
        } else if (response.body.errorType === 'REQUEST ERROR') {
          console.log(response.body.errorMessage)
          console.log('Appts field:');
          console.log(response.body.appts);
          let problem = vue.tableData.find(x => x.id === response.body.id);
          console.log('Problem location:');
          console.log(problem);
          this.errorMessage = 'This was an error getting the appointment times.'
          this.$bvModal.show('error-modal')
        } else {
          console.log('Error during appointments request');
          console.log(response.body.appts);
          this.errorMessage = 'This was an error getting the appointment times.'
          this.$bvModal.show('error-modal')
        }
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

  <div class="container">
    <h1>HRM Vaccine Appointments</h1>
    <p>Book online with a N.S Health card <a target="_blank" rel="noopener noreferrer" href="https://novascotia.flow.canimmunize.ca/en/9874123-19-7418965">here</a> or book by phone at <a href="tel:+1-833-797-7772">1-833-797-7772</a>.</p>
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
        <template #cell(address)="data">
          <a 
            :href="'https://www.google.com/maps/search/' + data.value.replace(/\s/g,'+')"
            target="_blank"
            rel="noopener noreferrer"
          >
            {{ data.value }}
          </a>
          <b-button @click="copyAddress(data.value)">
            copy
          </b-button>
        </template>
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
    <p v-if="hrm"><a href="/?all=true">See all appointments.</a></p>
    <p v-if="!hrm"><a href="/">Just see HRM appointments.</a></p>
    <p>Made with ❤️ by <a target="_blank" rel="noopener noreferrer" href="http://github.com/gwoods22/">Graeme Woods</a></p>
  </footer>
</div>
</template>
<style>
ul {
  list-style-type: none;
  padding: 0;
}
.modal ul {
  max-height: calc(100vh - 15rem);
}
.table button {
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
</style>
