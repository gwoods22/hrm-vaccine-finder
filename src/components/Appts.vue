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
        isBusy: true,
        loadingDirections: true,
        tableData: [
          {
            appointmentTime: "2",
            address: "-",
            distance: "-",
            name: "-",
            id: 2
          },
          {
            appointmentTime: "1",
            address: "-",
            distance: "-",
            name: "-",
            id: 1
          }

        ],
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
            key: 'vaccine',
            sortable: true
          },
        ]
      }
  },
  props: {
    msg: String
  },
  mounted () {
    const vue = this;

    let before = new Date
    
    request.get({
      'headers': headers,
      'url': AWS_URL + 'locations'
    }, (error, response) => {
      if (error) throw new Error(error);
      
      let locations = JSON.parse(response.body).locations;
      vue.tableData = locations;
      vue.isBusy = false;

      let middle = new Date
      console.log(locations);
      console.log((middle - before)/1000+ ' seconds for request 1');
      
      for (let i=0; i<locations.length; i++) {
        locations[i].gisFields = locations[i].gisLocationString.split(',').length
      }

      let addresses = locations.map(x => ({
        gisLocationString: x.gisLocationString,
        id: x.id
      }));

      let body = { 
        addresses: addresses 
      }
      request.post({
        'headers': headers,
        'url': AWS_URL + 'distance',
        'body': body,
        'json': true
      }, (error, response) => {
        if (error) throw new Error(error);
        vue.loadingDirections = false;

        let distances = response.body;
        console.log(distances);

        let after = new Date
        console.log((after - middle)/1000+ ' seconds for request 2');

        for (let i=0; i<locations.length; i++) {
          let dist = distances.find(x => x.id === locations[i].id);
          locations[i].distance = dist.distance;
          locations[i].rawDistance = dist.rawDistance;
        }

        console.log(locations);
      });  
    })
  }
}
</script>
<template>
    <div class="container">
      <h1>Vaccine Appointments</h1>
      <div class="flex" v-if="loadingDirections">
        <div>Getting Distances</div>
        <div><b-spinner label="Loading..."></b-spinner></div>
      </div>
      <div>
        <b-table 
          striped
          hover
          :items="tableData"
          :fields="fields"
          :busy="isBusy"
          primary-key="id"
        >
          <template #cell(address)="data">
            <a :href="'https://www.google.com/maps/search/' + data.value.replace(' ','+')" target="_blank" rel="noopener noreferrer">{{ data.value }}</a>
          </template>
        </b-table>
      </div>
    </div>
</template>
<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
h3 {
  margin: 40px 0 0;
}
ul {
  list-style-type: none;
  padding: 0;
}
li {
  display: inline-block;
  margin: 0 10px;
}
a {
  color: #42b983;
}
</style>
